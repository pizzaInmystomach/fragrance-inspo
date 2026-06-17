import json
import os
import time
import re
from collections import Counter
from langchain.prompts import PromptTemplate
from .llm_config import get_balanced_model, get_fast_model
from .prompts import (
    INPUT_PARSING_PROMPT,
    SCENE_PROMPT,
    MATCHING_PROMPT,
    DESCRIPTION_PROMPT,
    TRAIT_ENHANCEMENT_PROMPT,
)


class CharacterAnalyzer:
    """Scene/environment analyzer and fragrance matcher with intelligent input parsing"""

    def __init__(self):
        self.llm = get_balanced_model()
        self.fast_llm = get_fast_model()

        # 建立提示詞模板
        self.input_parsing_prompt = PromptTemplate(
            template=INPUT_PARSING_PROMPT, input_variables=["user_input"]
        )
        self.scene_prompt = PromptTemplate(
            template=SCENE_PROMPT, input_variables=["scene_prompt"]
        )
        self.matching_prompt = PromptTemplate(
            template=MATCHING_PROMPT,
            input_variables=[
                "character_analysis",
                "fragrances_data",
                "num_recommendations",
            ],
        )
        self.description_prompt = PromptTemplate(
            template=DESCRIPTION_PROMPT,
            input_variables=[
                "fragrance_name",
                "brand",
                "top_notes",
                "heart_notes",
                "base_notes",
                "accords",
            ],
        )
        self.trait_enhancement_prompt = PromptTemplate(
            template=TRAIT_ENHANCEMENT_PROMPT,
            input_variables=[
                "fragrance_name",
                "brand",
                "existing_accords",
                "notes_info",
            ],
        )

        # 使用新的 LCEL 語法建立鏈
        self.input_parsing_chain = self.input_parsing_prompt | self.fast_llm
        self.scene_chain = self.scene_prompt | self.llm
        self.description_chain = self.description_prompt | self.llm
        self.trait_enhancement_chain = self.trait_enhancement_prompt | self.fast_llm
        self.last_generation_tokens = 0
        self.require_llm = os.getenv("REQUIRE_LLM_RECOMMENDATIONS", "true").lower() in (
            "1",
            "true",
            "yes",
        )

    def reset_generation_metrics(self):
        """Reset token counters before measuring a generation stage."""
        self.last_generation_tokens = 0

    def _extract_output_tokens(self, result):
        """Best-effort extraction of output token count from LangChain responses."""
        usage = getattr(result, "usage_metadata", None)
        if isinstance(usage, dict):
            output_tokens = usage.get("output_tokens")
            if isinstance(output_tokens, int):
                return output_tokens

        metadata = getattr(result, "response_metadata", None)
        if isinstance(metadata, dict):
            token_usage = metadata.get("token_usage", {})
            if isinstance(token_usage, dict):
                for key in ("completion_tokens", "output_tokens", "generated_tokens"):
                    output_tokens = token_usage.get(key)
                    if isinstance(output_tokens, int):
                        return output_tokens

        return 0

    def _safe_llm_call_with_usage(self, chain, inputs, retries=2, delay=1):
        """安全的 LLM 調用，並記錄 output token 數。"""
        for attempt in range(retries + 1):
            try:
                if attempt > 0:
                    print(f"重試第 {attempt} 次...")
                    time.sleep(delay * attempt)

                result = chain.invoke(inputs)
                content = result.content if hasattr(result, "content") else str(result)
                output_tokens = self._extract_output_tokens(result)
                self.last_generation_tokens += output_tokens

                return {
                    "content": content.strip(),
                    "output_tokens": output_tokens,
                }

            except Exception as e:
                error_msg = str(e).lower()
                if "model_decommissioned" in error_msg or "decommissioned" in error_msg:
                    print(
                        "LLM 模型已不可用，請更新 llm_config.py "
                        "或 GEMINI_*_MODEL 環境變數。"
                    )
                    return {"content": None, "output_tokens": 0}

                if "429" in error_msg or "rate limit" in error_msg:
                    print(f"API 限制錯誤，等待 {delay * (attempt + 1)} 秒...")
                    if attempt < retries:
                        time.sleep(delay * (attempt + 1))
                        continue
                print(f"LLM 調用失敗 (嘗試 {attempt + 1}): {str(e)}")
                if attempt == retries:
                    return {"content": None, "output_tokens": 0}
        return {"content": None, "output_tokens": 0}

    def _clean_text(self, value):
        """Normalize string/list values from MongoDB fragrance documents."""
        if isinstance(value, list):
            return ", ".join(str(item).strip() for item in value if str(item).strip())
        if value is None:
            return ""
        return str(value).replace(",", ", ").strip()

    def _safe_llm_call(self, chain, inputs, retries=2, delay=1):
        """安全的 LLM 調用，包含重試機制和錯誤處理"""
        result = self._safe_llm_call_with_usage(chain, inputs, retries, delay)
        return result["content"]

    def _require_llm_content(self, content, stage):
        if content:
            return content
        if self.require_llm:
            raise RuntimeError(
                f"{stage} requires a successful LLM response. "
                "Check GEMINI_API_KEY and GEMINI_*_MODEL settings."
            )
        return None

    def _extract_json_from_text(self, text):
        """從文本中提取 JSON - 強化版本（修復引號問題）"""
        if not text:
            return None

        # 第一步：移除常見的前綴文字
        prefixes_to_remove = [
            "Here is the analysis",
            "Here is the",
            "The analysis is",
            "Analysis:",
            "Response:",
            "Result:",
        ]

        cleaned_text = text.strip()
        for prefix in prefixes_to_remove:
            if cleaned_text.lower().startswith(prefix.lower()):
                colon_pos = cleaned_text.find(":")
                if colon_pos != -1:
                    cleaned_text = cleaned_text[colon_pos + 1 :].strip()
                break

        # 第二步：移除 markdown 包裝
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
        cleaned_text = cleaned_text.strip()

        # 第三步：修復常見的引號問題
        if '"analysis":' in cleaned_text or '"message":' in cleaned_text:
            # 檢查字符串字段是否正確結束
            for field in ['"analysis":', '"message":', '"intent":']:
                if field in cleaned_text:
                    field_start = cleaned_text.find(field)
                    if field_start != -1:
                        # 找到字段值的開始
                        value_start = cleaned_text.find('"', field_start + len(field))
                        if value_start != -1:
                            # 找到字符串的結束
                            remaining = cleaned_text[value_start + 1 :]

                            # 如果沒有找到結束引號在 '}' 之前，添加一個
                            closing_brace = remaining.find("}")
                            closing_quote = remaining.find('"')

                            if closing_brace != -1 and (
                                closing_quote == -1 or closing_quote > closing_brace
                            ):
                                # 需要添加結束引號
                                insert_pos = value_start + 1 + closing_brace
                                cleaned_text = (
                                    cleaned_text[:insert_pos]
                                    + '"'
                                    + cleaned_text[insert_pos:]
                                )
                                break

        # 第四步：直接嘗試解析
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            pass

        # 第五步：使用正則表達式找到 JSON 對象
        json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
        matches = re.findall(json_pattern, cleaned_text, re.DOTALL)

        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue

        # 第六步：修復截斷的 JSON（保持原有邏輯）
        if "{" in cleaned_text and (
            '"traits"' in cleaned_text or '"status"' in cleaned_text
        ):
            try:
                start_pos = cleaned_text.find("{")
                json_part = cleaned_text[start_pos:]

                if json_part.count("{") > json_part.count("}"):
                    lines = json_part.split("\n")
                    fixed_lines = []

                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue

                        if line == "{":
                            fixed_lines.append(line)
                        elif (
                            line
                            and ":" in line
                            and (line.endswith(",") or line.endswith('"'))
                        ):
                            fixed_lines.append(line)
                        elif line and line.startswith('"') and ":" in line:
                            if not line.endswith('"') and not line.endswith(","):
                                quote_pos = line.rfind('"')
                                if quote_pos > line.find(":"):
                                    line = line[: quote_pos + 1]
                                else:
                                    if "analysis" in line or "message" in line:
                                        line = f'{line.split(":")[0]}: "Default description"'
                                    else:
                                        continue
                            fixed_lines.append(line)

                    if fixed_lines and fixed_lines[-1] != "}":
                        if fixed_lines[-1].endswith(","):
                            fixed_lines[-1] = fixed_lines[-1][:-1]
                        fixed_lines.append("}")

                    fixed_json = "\n".join(fixed_lines)
                    return json.loads(fixed_json)

            except Exception:
                pass

        return None

    def parse_user_input(self, user_input):
        """解析用戶輸入，提取情境、環境、氣味需求"""
        try:
            print(f"🔍 解析情境輸入: '{user_input}'")

            # 首先嘗試基本的情境/氣味關鍵詞檢測（快速路徑）
            quick_parse = self._quick_scene_detection(user_input)
            if quick_parse:
                print(f"✅ 快速檢測成功: {quick_parse['scene_prompt']}")
                return quick_parse

            # 使用 LLM 進行智能解析
            content = self._safe_llm_call(
                self.input_parsing_chain, {"user_input": user_input}
            )

            if content:
                print(f"📝 LLM 解析回應: '{content[:100]}...'")
                parsed_result = self._extract_json_from_text(content)

                if parsed_result and isinstance(parsed_result, dict):
                    print(f"✅ LLM 解析成功: {parsed_result.get('status')}")
                    return parsed_result

            # 如果 LLM 解析失敗，使用備用邏輯
            print(f"⚠️ LLM 解析失敗，使用備用邏輯")
            return self._fallback_input_parsing(user_input)

        except Exception as e:
            print(f"❌ 輸入解析錯誤: {str(e)}")
            return self._fallback_input_parsing(user_input)

    def _quick_scene_detection(self, user_input):
        """快速檢測常見情境與氣味線索"""
        input_lower = user_input.lower()

        scene_keywords = [
            "rain",
            "rainy",
            "library",
            "book",
            "pages",
            "old book",
            "earth",
            "earthy",
            "wood",
            "woody",
            "forest",
            "cabin",
            "winter",
            "summer",
            "beach",
            "garden",
            "coffee",
            "tea",
            "smoky",
            "incense",
            "clean",
            "fresh",
            "cozy",
            "romantic",
            "office",
            "night",
            "morning",
            "雨",
            "雨天",
            "圖書館",
            "書",
            "木質",
            "泥土",
            "森林",
            "咖啡",
        ]

        if any(keyword in input_lower for keyword in scene_keywords):
            cleaned_prompt = user_input.strip()
            return {
                "status": "success",
                "scene_prompt": cleaned_prompt,
                "intent": "User wants fragrance recommendations for a scene or scent atmosphere",
                "message": "Great! I'll find fragrances that match this scene and atmosphere.",
            }

        return None

    def _fallback_input_parsing(self, user_input):
        """備用輸入解析邏輯"""
        input_lower = user_input.lower().strip()

        # 檢查是否是問候或無關內容
        greetings = [
            "hello",
            "hi",
            "hey",
            "good morning",
            "good evening",
            "how are you",
            "thanks",
            "thank you",
            "goodbye",
            "bye",
            "have a nice day",
        ]

        if any(greeting in input_lower for greeting in greetings):
            return {
                "status": "invalid",
                "scene_prompt": None,
                "intent": "Casual conversation",
                "message": "Hello! Tell me a scene, environment, mood, or scent brief, such as 'rainy library' or 'woody, earthy old book pages'.",
            }

        vague_phrases = ["something nice", "anything", "perfume", "fragrance", "scent"]
        if input_lower in vague_phrases or len(input_lower) < 4:
            return {
                "status": "need_clarification",
                "scene_prompt": None,
                "intent": "User asked for fragrance but did not provide enough scene details",
                "message": "I'd love to help you find a fragrance. Please add a scene, environment, mood, or scent notes, for example: 'rainy library with old book pages and damp wood'.",
            }

        if len(input_lower.split()) <= 3:
            return {
                "status": "success",
                "scene_prompt": user_input.strip(),
                "intent": "User provided a concise scene or scent prompt",
                "message": "Great! I'll use this as the fragrance atmosphere prompt.",
            }

        return {
            "status": "success",
            "scene_prompt": user_input.strip(),
            "intent": "User provided a fragrance scene or scent brief",
            "message": "Great! I'll find fragrances that match this scene and atmosphere.",
        }

    def analyze_scene(self, scene_prompt):
        """Analyze scene/environment scent traits (同步版本)"""
        try:
            print(f"🔍 開始分析情境: {scene_prompt}")

            content = self._safe_llm_call(
                self.scene_chain,
                {"scene_prompt": scene_prompt},
            )
            content = self._require_llm_content(content, "Scene analysis")

            if not content:
                print(f"⚠️ LLM 調用失敗，使用預設情境分析")
                return self._get_default_scene_analysis(scene_prompt)

            print(f"📝 LLM 原始回應 (前100字符): '{content[:100]}...'")

            # 嘗試解析 JSON
            parsed_result = self._extract_json_from_text(content)

            if parsed_result and isinstance(parsed_result, dict):
                required_fields = ["traits", "style", "analysis"]
                missing_fields = [
                    field for field in required_fields if field not in parsed_result
                ]

                if not missing_fields:
                    print(f"✅ JSON 解析成功")
                    return parsed_result
                else:
                    print(f"⚠️ JSON 結構不完整，缺少字段: {missing_fields}")
            else:
                print(f"⚠️ JSON 解析失敗")

            if self.require_llm:
                raise RuntimeError("Scene analysis LLM response was not valid JSON.")

            return self._get_default_scene_analysis(scene_prompt)

        except Exception as e:
            print(f"❌ 情境分析錯誤: {str(e)}")
            if self.require_llm:
                raise
            return self._get_default_scene_analysis(scene_prompt)

    def analyze_character(self, character_name, source_type=""):
        """Backward-compatible wrapper now treating input as a scene prompt."""
        scene_prompt = character_name
        if source_type:
            scene_prompt = f"{character_name} ({source_type})"
        return self.analyze_scene(scene_prompt)

    def _get_default_scene_analysis(self, scene_prompt):
        """根據情境提示提供智能預設分析"""
        prompt_lower = scene_prompt.lower()
        traits = ["atmospheric", "evocative", "balanced", "memorable", "textured"]

        scene_traits_map = {
            "rain": ["damp", "mineral", "fresh", "earthy", "introspective"],
            "rainy": ["damp", "mineral", "fresh", "earthy", "introspective"],
            "雨": ["damp", "mineral", "fresh", "earthy", "introspective"],
            "library": ["woody", "paper-like", "dusty", "quiet", "scholarly"],
            "圖書館": ["woody", "paper-like", "dusty", "quiet", "scholarly"],
            "book": ["paper-like", "dry", "woody", "nostalgic", "intimate"],
            "書": ["paper-like", "dry", "woody", "nostalgic", "intimate"],
            "earth": ["earthy", "rooty", "grounded", "damp", "natural"],
            "泥土": ["earthy", "rooty", "grounded", "damp", "natural"],
            "wood": ["woody", "dry", "warm", "grounded", "textured"],
            "木": ["woody", "dry", "warm", "grounded", "textured"],
            "coffee": ["roasted", "warm", "bitter", "cozy", "dark"],
            "咖啡": ["roasted", "warm", "bitter", "cozy", "dark"],
        }

        for key, mapped_traits in scene_traits_map.items():
            if key in prompt_lower:
                traits = mapped_traits
                break

        style_map = {
            "damp": ["quiet", "naturalistic"],
            "woody": ["grounded", "textural"],
            "paper-like": ["nostalgic", "academic"],
            "earthy": ["organic", "grounded"],
            "roasted": ["cozy", "dark"],
            "fresh": ["clean", "transparent"],
        }

        style = ["atmospheric", "wearable"]
        for trait in traits:
            if trait in style_map:
                style = style_map[trait]
                break

        return {
            "traits": traits,
            "style": style,
            "analysis": f"This prompt suggests a {', '.join(traits[:3])} fragrance atmosphere with a {', '.join(style)} style.",
        }

    def _get_default_character_analysis(self, character_name):
        """Backward-compatible alias for older callers."""
        return self._get_default_scene_analysis(character_name)

    # 保持其他原有方法不變...
    def enhance_fragrance_data(self, fragrance):
        """使用LLM增強香水資料，補充缺失的traits等資訊"""
        try:
            # 準備現有資訊
            name = self._clean_text(fragrance.get("Name", "")).replace(",", "").strip()
            brand = self._clean_text(fragrance.get("Brand", "")).replace(",", "").strip()
            existing_accords = self._clean_text(fragrance.get("Accords", ""))

            # 处理Notes对象
            notes_obj = fragrance.get("Notes", {})
            top_notes = self._clean_text(fragrance.get("top_notes") or notes_obj.get("Top Notes", ""))
            heart_notes = self._clean_text(fragrance.get("heart_notes") or notes_obj.get("Middle Notes", "") or notes_obj.get("Heart Notes", ""))
            base_notes = self._clean_text(fragrance.get("base_notes") or notes_obj.get("Base Notes", ""))

            notes_info = f"Top: {top_notes}, Heart: {heart_notes}, Base: {base_notes}"

            # 使用LLM生成增强信息
            content = self._safe_llm_call(
                self.trait_enhancement_chain,
                {
                    "fragrance_name": name,
                    "brand": brand,
                    "existing_accords": existing_accords,
                    "notes_info": notes_info,
                },
            )

            enhancement_data = None
            if content:
                enhancement_data = self._extract_json_from_text(content)

            if not enhancement_data or not isinstance(enhancement_data, dict):
                enhancement_data = self._get_basic_enhancement_data(existing_accords)

            # 合并原始数据和增强数据
            enhanced_fragrance = {
                "id": str(fragrance.get("_id")),
                "Name": name,
                "Brand": brand,
                "Accords": existing_accords.split(", ") if existing_accords else [],
                "top_notes": top_notes.split(", ") if top_notes else [],
                "heart_notes": heart_notes.split(", ") if heart_notes else [],
                "base_notes": base_notes.split(", ") if base_notes else [],
                "additional_traits": enhancement_data.get("additional_traits", []),
                "personality_match": enhancement_data.get("personality_match", []),
                "mood_description": enhancement_data.get("mood_description", ""),
                "season_suitability": enhancement_data.get("season_suitability", []),
                "time_of_day": enhancement_data.get("time_of_day", []),
            }

            return enhanced_fragrance

        except Exception as e:
            print(f"Fragrance enhancement error: {str(e)}")
            # 返回基本的增强版本
            return self._create_basic_enhanced_fragrance(fragrance)

    def _get_basic_enhancement_data(self, accords):
        """根據香調生成基本增強數據"""
        accords_lower = accords.lower() if accords else ""

        if any(word in accords_lower for word in ["floral", "rose", "jasmine", "lily"]):
            return {
                "additional_traits": ["romantic", "feminine", "elegant"],
                "personality_match": ["gentle", "nurturing", "graceful"],
                "mood_description": "Romantic and elegant fragrance",
                "season_suitability": ["spring", "summer"],
                "time_of_day": ["day", "evening"],
            }
        elif any(word in accords_lower for word in ["woody", "sandalwood", "cedar"]):
            return {
                "additional_traits": ["sophisticated", "grounded", "classic"],
                "personality_match": ["confident", "reliable", "mature"],
                "mood_description": "Sophisticated woody fragrance",
                "season_suitability": ["autumn", "winter"],
                "time_of_day": ["evening", "night"],
            }
        elif any(word in accords_lower for word in ["animal", "smoky", "leather"]):
            return {
                "additional_traits": ["edgy", "unconventional", "bold"],
                "personality_match": ["rebellious", "adventurous", "confident"],
                "mood_description": "Intense, bold, and unapologetic",
                "season_suitability": ["autumn", "winter"],
                "time_of_day": ["evening", "night"],
            }
        else:
            return {
                "additional_traits": ["sophisticated", "elegant", "modern"],
                "personality_match": ["confident", "artistic", "refined"],
                "mood_description": "Sophisticated fragrance",
                "season_suitability": ["spring", "summer"],
                "time_of_day": ["day", "evening"],
            }

    def _create_basic_enhanced_fragrance(self, fragrance):
        """创建基本的增强香水数据"""
        notes_obj = fragrance.get("Notes", {})
        accords = self._clean_text(fragrance.get("Accords", ""))
        top_notes = self._clean_text(fragrance.get("top_notes") or notes_obj.get("Top Notes", ""))
        heart_notes = self._clean_text(fragrance.get("heart_notes") or notes_obj.get("Middle Notes", "") or notes_obj.get("Heart Notes", ""))
        base_notes = self._clean_text(fragrance.get("base_notes") or notes_obj.get("Base Notes", ""))

        enhancement_data = self._get_basic_enhancement_data(accords)

        return {
            "id": str(fragrance.get("_id")),
            "Name": self._clean_text(fragrance.get("Name", "")).replace(",", "").strip(),
            "Brand": self._clean_text(fragrance.get("Brand", "")).replace(",", "").strip(),
            "Accords": accords.split(", ") if accords else [],
            "top_notes": top_notes.split(", ") if top_notes else [],
            "heart_notes": heart_notes.split(", ") if heart_notes else [],
            "base_notes": base_notes.split(", ") if base_notes else [],
            "additional_traits": enhancement_data.get("additional_traits", []),
            "personality_match": enhancement_data.get("personality_match", []),
            "mood_description": enhancement_data.get("mood_description", ""),
            "season_suitability": enhancement_data.get("season_suitability", []),
            "time_of_day": enhancement_data.get("time_of_day", []),
        }

    def rank_fragrances_locally(
        self, scene_prompt, scene_analysis, fragrances, top_k=5
    ):
        """Rank MongoDB candidates locally using weighted lexical relevance."""
        top_k = max(1, int(top_k))
        query_terms = self._tokenize_relevance_text(
            " ".join(
                [
                    scene_prompt,
                    " ".join(scene_analysis.get("traits", [])),
                    " ".join(scene_analysis.get("style", [])),
                    scene_analysis.get("analysis", ""),
                ]
            )
        )
        query_counts = Counter(query_terms)

        weighted_fields = (
            ("Accords", 4.0),
            ("main_accords", 4.0),
            ("top_notes", 3.0),
            ("heart_notes", 3.0),
            ("base_notes", 3.0),
            ("Notes", 3.0),
            ("Name", 1.5),
            ("Brand", 0.5),
        )

        scored = []
        for position, fragrance in enumerate(fragrances):
            score = 0.0
            for field, weight in weighted_fields:
                field_terms = Counter(
                    self._tokenize_relevance_text(fragrance.get(field, ""))
                )
                score += weight * sum(
                    min(count, field_terms.get(term, 0))
                    for term, count in query_counts.items()
                )

            scored.append((score, -position, fragrance))

        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
        selected = [item[2] for item in scored[:top_k]]

        print(
            f"本地文字相關度排序完成：從 {len(fragrances)} 筆候選取 top {len(selected)}"
        )
        return selected

    def _tokenize_relevance_text(self, value):
        text = self._clean_text(value).lower()
        return re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?|[\u4e00-\u9fff]+", text)

    def match_fragrances(self, character_analysis, fragrances, num_recommendations=3):
        """Use the LLM to match one candidate batch."""
        try:
            print(f"🔄 開始處理 {len(fragrances)} 個香水...")

            enhanced_fragrances = [
                self._create_basic_enhanced_fragrance(fragrance)
                for fragrance in fragrances
            ]

            print(f"✅ 完成香水增強處理")
            return self._match_enhanced_fragrances(
                character_analysis,
                enhanced_fragrances,
                num_recommendations,
            )
        except Exception as e:
            print(f"❌ 香水匹配錯誤: {str(e)}")
            if self.require_llm:
                raise
            return self._generate_smart_recommendations(
                enhanced_fragrances if "enhanced_fragrances" in locals() else [],
                character_analysis,
                num_recommendations,
            )

    def match_fragrance_batches(
        self, character_analysis, fragrance_batches, num_recommendations=3
    ):
        """Run LLM matching per batch, then rerank all batch winners with the LLM."""
        finalists = []
        total_batches = len(fragrance_batches)

        for index, batch in enumerate(fragrance_batches, 1):
            print(f"🤖 LLM 匹配批次 {index}/{total_batches}，候選 {len(batch)} 筆")
            batch_result = self.match_fragrances(
                character_analysis,
                batch,
                num_recommendations=num_recommendations,
            )
            finalists.extend(
                rec["fragrance"]
                for rec in batch_result.get("recommendations", [])
                if rec.get("fragrance")
            )

        if not finalists:
            return {"recommendations": []}

        rerank_batch_size = 50
        round_number = 1

        while len(finalists) > rerank_batch_size:
            next_round = []
            groups = [
                finalists[index : index + rerank_batch_size]
                for index in range(0, len(finalists), rerank_batch_size)
            ]
            print(
                f"🏁 LLM 淘汰排名第 {round_number} 輪："
                f"{len(finalists)} 個候選，分成 {len(groups)} 組"
            )

            for group in groups:
                group_result = self._match_enhanced_fragrances(
                    character_analysis,
                    group,
                    num_recommendations,
                )
                next_round.extend(
                    rec["fragrance"]
                    for rec in group_result.get("recommendations", [])
                    if rec.get("fragrance")
                )

            finalists = next_round
            round_number += 1

        print(f"🏁 LLM 最終排名，共 {len(finalists)} 個批次優勝候選")
        return self._match_enhanced_fragrances(
            character_analysis,
            finalists,
            num_recommendations,
        )

    def _match_enhanced_fragrances(
        self, character_analysis, enhanced_fragrances, num_recommendations
    ):
        try:
            # Format fragrance data for LLM
            fragrances_text = "\n".join(
                [
                    f"ID: {f['id']}, Name: {f['Name']}, Brand: {f['Brand']}, "
                    f"Accords: {', '.join(f['Accords'])}, "
                    f"Top Notes: {', '.join(f['top_notes'])}, "
                    f"Heart Notes: {', '.join(f['heart_notes'])}, "
                    f"Base Notes: {', '.join(f['base_notes'])}, "
                    f"Additional Traits: {', '.join(f['additional_traits'])}, "
                    f"Personality Match: {', '.join(f['personality_match'])}"
                    for f in enhanced_fragrances
                ]
            )

            # 動態建立匹配鏈
            matching_chain = self.matching_prompt | self.llm

            print(f"🤖 開始 LLM 匹配分析...")
            content = self._safe_llm_call(
                matching_chain,
                {
                    "character_analysis": json.dumps(character_analysis),
                    "fragrances_data": fragrances_text,
                    "num_recommendations": num_recommendations,
                },
            )
            content = self._require_llm_content(content, "Fragrance matching")

            if content:
                print(f"📝 匹配 LLM 回應:")
                print(f"長度: {len(content)} 字符")
                print(f"前 200 字符: '{content[:200]}...'")

                match_result = self._extract_json_from_text(content)

                if (
                    match_result
                    and isinstance(match_result, dict)
                    and "recommendations" in match_result
                ):
                    print(f"✅ LLM 匹配成功")
                    return self._process_llm_recommendations(
                        match_result, enhanced_fragrances, character_analysis
                    )

            if self.require_llm:
                raise RuntimeError("Fragrance matching LLM response was not valid JSON.")

            print(f"⚠️ LLM 匹配失敗，使用備用邏輯")
            return self._generate_smart_recommendations(
                enhanced_fragrances, character_analysis, num_recommendations
            )

        except Exception as e:
            print(f"❌ 香水匹配錯誤: {str(e)}")
            if self.require_llm:
                raise
            return self._generate_smart_recommendations(
                enhanced_fragrances,
                character_analysis,
                num_recommendations,
            )

    def _process_llm_recommendations(
        self, match_result, enhanced_fragrances, character_analysis
    ):
        """處理 LLM 返回的推薦結果"""
        recommendations = match_result.get("recommendations", [])
        processed_recommendations = []

        for i, rec in enumerate(recommendations):
            fragrance_id = rec.get("fragrance_id")
            rationale = rec.get(
                "rationale", "This fragrance matches the requested scene and atmosphere."
            )

            # 尋找對應的香水
            matched_fragrance = next(
                (f for f in enhanced_fragrances if f["id"] == fragrance_id),
                (
                    enhanced_fragrances[i]
                    if i < len(enhanced_fragrances)
                    else enhanced_fragrances[0]
                ),
            )

            processed_recommendations.append(
                {
                    "fragrance": matched_fragrance,
                    "rationale": rationale,
                    "rank": i + 1,
                    "match_score": 5 - i,
                }
            )

        return {"recommendations": processed_recommendations}

    def _generate_smart_recommendations(
        self, enhanced_fragrances, character_analysis, num_recommendations
    ):
        """生成智能推薦"""
        if not enhanced_fragrances:
            return {"recommendations": []}

        print(f"🔄 使用智能邏輯生成推薦...")
        recommendations = []

        character_traits = character_analysis.get("traits", [])
        character_style = character_analysis.get("style", [])

        # 為每個香水計算匹配分數
        scored_fragrances = []
        for fragrance in enhanced_fragrances:
            score = self._calculate_match_score(
                fragrance, character_traits, character_style
            )
            scored_fragrances.append((fragrance, score))

        # 按分數排序
        scored_fragrances.sort(key=lambda x: x[1], reverse=True)

        # 生成推薦
        for i, (fragrance, score) in enumerate(scored_fragrances[:num_recommendations]):
            rationale = self._generate_smart_rationale(fragrance, character_analysis)

            recommendations.append(
                {
                    "fragrance": fragrance,
                    "rationale": rationale,
                    "rank": i + 1,
                    "match_score": score,
                }
            )

        return {"recommendations": recommendations}

    def _calculate_match_score(self, fragrance, character_traits, character_style):
        """智能計算匹配分數"""
        score = 0

        fragrance_traits = (
            fragrance.get("additional_traits", [])
            + fragrance.get("personality_match", [])
            + fragrance.get("Accords", [])
            + fragrance.get("top_notes", [])
            + fragrance.get("heart_notes", [])
            + fragrance.get("base_notes", [])
        )
        for trait in character_traits:
            if any(trait.lower() in ft.lower() for ft in fragrance_traits):
                score += 2

        for style in character_style:
            if any(style.lower() in ft.lower() for ft in fragrance_traits):
                score += 1

        return score

    def _generate_smart_rationale(self, fragrance, character_analysis):
        """生成智能推薦理由"""
        name = fragrance.get("Name", "")
        traits = character_analysis.get("traits", [])
        accords = fragrance.get("Accords", [])
        personality_match = fragrance.get("personality_match", [])

        if personality_match and traits:
            common_traits = [
                t
                for t in traits
                if any(t.lower() in pm.lower() for pm in personality_match)
            ]
            if common_traits:
                return f"The {', '.join(common_traits[:2])} nature perfectly aligns with {name}'s {', '.join(personality_match[:2])} qualities."

        if accords:
            return f"{name}'s distinctive {', '.join(accords[:3])} blend fits the requested atmosphere and sensory setting."

        return f"This fragrance's distinctive profile makes it a fitting match for the requested scene."

    def match_fragrance(self, character_analysis, fragrances):
        """Match single fragrance (向後兼容)"""
        result = self.match_fragrances(
            character_analysis, fragrances, num_recommendations=1
        )
        if result and result.get("recommendations"):
            return result["recommendations"][0]
        return {
            "fragrance": (
                self._create_basic_enhanced_fragrance(fragrances[0])
                if fragrances
                else None
            ),
            "rationale": "This fragrance's traits match the requested scene and atmosphere.",
        }

    def generate_description(self, fragrance):
        """Generate fragrance description (同步版本)"""
        try:
            content = self._safe_llm_call(
                self.description_chain,
                {
                    "fragrance_name": fragrance["Name"],
                    "brand": fragrance["Brand"],
                    "top_notes": ", ".join(fragrance.get("top_notes", [])),
                    "heart_notes": ", ".join(fragrance.get("heart_notes", [])),
                    "base_notes": ", ".join(fragrance.get("base_notes", [])),
                    "accords": ", ".join(fragrance.get("Accords", [])),
                }
            )
            content = self._require_llm_content(content, "Description generation")

            if content:
                return content.strip()

        except Exception as e:
            print(f"Description generation error: {str(e)}")
            if self.require_llm:
                raise

        return f"{fragrance['Name']} by {fragrance.get('Brand', 'Unknown Brand')} is a captivating fragrance that embodies elegance and sophistication. This unique scent offers a harmonious blend of carefully selected notes that create an unforgettable olfactory experience."
