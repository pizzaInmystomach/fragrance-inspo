import json
import time
import re
from langchain.prompts import PromptTemplate
from .llm_config import get_balanced_model, get_fast_model
from .prompts import (
    INPUT_PARSING_PROMPT,
    CHARACTER_PROMPT,
    MATCHING_PROMPT,
    DESCRIPTION_PROMPT,
    TRAIT_ENHANCEMENT_PROMPT,
)


class CharacterAnalyzer:
    """Character analyzer and fragrance matcher with intelligent input parsing"""

    def __init__(self):
        self.llm = get_balanced_model()
        self.fast_llm = get_fast_model()

        # 建立提示詞模板
        self.input_parsing_prompt = PromptTemplate(
            template=INPUT_PARSING_PROMPT, input_variables=["user_input"]
        )
        self.character_prompt = PromptTemplate(
            template=CHARACTER_PROMPT, input_variables=["character_name", "source_type"]
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
        self.character_chain = self.character_prompt | self.llm
        self.description_chain = self.description_prompt | self.llm
        self.trait_enhancement_chain = self.trait_enhancement_prompt | self.fast_llm

    def _safe_llm_call(self, chain, inputs, retries=2, delay=1):
        """安全的 LLM 調用，包含重試機制和錯誤處理"""
        for attempt in range(retries + 1):
            try:
                if attempt > 0:
                    print(f"重試第 {attempt} 次...")
                    time.sleep(delay * attempt)

                result = chain.invoke(inputs)
                content = result.content if hasattr(result, "content") else str(result)
                return content.strip()

            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "rate limit" in error_msg:
                    print(f"API 限制錯誤，等待 {delay * (attempt + 1)} 秒...")
                    if attempt < retries:
                        time.sleep(delay * (attempt + 1))
                        continue
                print(f"LLM 調用失敗 (嘗試 {attempt + 1}): {str(e)}")
                if attempt == retries:
                    return None
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
        """解析用戶輸入，提取角色信息"""
        try:
            print(f"🔍 解析用戶輸入: '{user_input}'")

            # 首先嘗試基本的關鍵詞檢測（快速路徑）
            quick_parse = self._quick_character_detection(user_input)
            if quick_parse:
                print(f"✅ 快速檢測成功: {quick_parse['character_name']}")
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

    def _quick_character_detection(self, user_input):
        """快速檢測常見角色名稱"""
        input_lower = user_input.lower()

        # 常見角色映射
        character_map = {
            # Harry Potter 系列
            "harry potter": {"name": "Harry Potter", "source": "Harry Potter"},
            "hermione granger": {"name": "Hermione Granger", "source": "Harry Potter"},
            "hermione": {"name": "Hermione Granger", "source": "Harry Potter"},
            "ron weasley": {"name": "Ron Weasley", "source": "Harry Potter"},
            "dumbledore": {"name": "Albus Dumbledore", "source": "Harry Potter"},
            "snape": {"name": "Severus Snape", "source": "Harry Potter"},
            # 經典文學
            "daisy buchanan": {"name": "Daisy Buchanan", "source": "The Great Gatsby"},
            "gatsby": {"name": "Jay Gatsby", "source": "The Great Gatsby"},
            "elizabeth bennet": {
                "name": "Elizabeth Bennet",
                "source": "Pride and Prejudice",
            },
            "mr darcy": {"name": "Mr. Darcy", "source": "Pride and Prejudice"},
            # 電影角色
            "audrey hepburn": {"name": "Audrey Hepburn", "source": "Classic Hollywood"},
            "marilyn monroe": {"name": "Marilyn Monroe", "source": "Classic Hollywood"},
            "james bond": {"name": "James Bond", "source": "James Bond"},
            # 中文角色
            "妙麗": {"name": "Hermione Granger", "source": "Harry Potter"},
            "哈利波特": {"name": "Harry Potter", "source": "Harry Potter"},
            "哈利": {"name": "Harry Potter", "source": "Harry Potter"},
        }

        # 檢查是否包含已知角色
        for character_key, character_info in character_map.items():
            if character_key in input_lower:
                return {
                    "status": "success",
                    "character_name": character_info["name"],
                    "source": character_info["source"],
                    "intent": f"User wants fragrance recommendation for {character_info['name']}",
                    "message": f"Great! I'll find fragrances that match {character_info['name']}'s personality.",
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
                "character_name": None,
                "source": None,
                "intent": "Casual conversation",
                "message": "Hello! I'm here to help you find fragrances that match fictional characters. Please tell me which character you'd like to smell like, for example: 'I want to smell like Hermione Granger' or 'What fragrance would Harry Potter wear?'",
            }

        # 檢查是否包含"smell like"但沒有明確角色
        if "smell like" in input_lower:
            if len(input_lower.split()) <= 4:  # 太短，可能缺少角色名
                return {
                    "status": "need_clarification",
                    "character_name": None,
                    "source": None,
                    "intent": "User wants to smell like someone but didn't specify who",
                    "message": "I'd love to help you find a fragrance! Could you please tell me which specific character you'd like to smell like? For example: 'Harry Potter', 'Hermione Granger', or 'Daisy Buchanan'.",
                }

        # 檢查是否是描述性詞語（brave, intelligent等）
        descriptive_words = [
            "brave",
            "intelligent",
            "elegant",
            "mysterious",
            "strong",
            "smart",
            "beautiful",
            "confident",
            "kind",
            "powerful",
        ]

        if (
            any(word in input_lower for word in descriptive_words)
            and len(input_lower.split()) <= 3
        ):
            return {
                "status": "need_clarification",
                "character_name": None,
                "source": None,
                "intent": "User described traits but no specific character",
                "message": "I understand you're looking for a fragrance for someone with those qualities! Could you please tell me a specific character name? For example: 'Hermione Granger' (intelligent), 'Harry Potter' (brave), or 'Daisy Buchanan' (elegant).",
            }

        # 如果輸入很短或看起來像角色名但不在已知列表中
        if len(input_lower.split()) <= 3 and len(input_lower) > 3:
            return {
                "status": "need_clarification",
                "character_name": input_lower.title(),  # 嘗試提取作為角色名
                "source": None,
                "intent": "Possible character name but needs confirmation",
                "message": f"Are you looking for fragrances that would match '{input_lower.title()}'? If so, could you please provide a bit more context about this character or confirm the spelling? This will help me give you better recommendations.",
            }

        # 默認情況
        return {
            "status": "need_clarification",
            "character_name": None,
            "source": None,
            "intent": "Unclear input",
            "message": "I'd love to help you find the perfect fragrance! Please tell me which fictional character you'd like to match. You can say something like: 'I want to smell like Harry Potter' or 'What fragrance would Hermione Granger wear?'",
        }

    # 保持原有的方法不變
    def analyze_character(self, character_name, source_type=""):
        """Analyze character traits (同步版本)"""
        try:
            print(f"🔍 開始分析角色: {character_name}")

            content = self._safe_llm_call(
                self.character_chain,
                {"character_name": character_name, "source_type": source_type},
            )

            if not content:
                print(f"⚠️ LLM 調用失敗，使用預設分析")
                return self._get_default_character_analysis(character_name)

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

            return self._get_default_character_analysis(character_name)

        except Exception as e:
            print(f"❌ 角色分析錯誤: {str(e)}")
            return self._get_default_character_analysis(character_name)

    def _get_default_character_analysis(self, character_name):
        """根據角色名稱提供智能預設分析"""
        character_traits_map = {
            "妙麗": ["intelligent", "studious", "brave", "loyal", "perfectionist"],
            "hermione": ["intelligent", "studious", "brave", "loyal", "perfectionist"],
            "hermione granger": [
                "intelligent",
                "studious",
                "brave",
                "loyal",
                "perfectionist",
            ],
            "哈利": ["brave", "loyal", "determined", "humble", "heroic"],
            "harry": ["brave", "loyal", "determined", "humble", "heroic"],
            "harry potter": ["brave", "loyal", "determined", "humble", "heroic"],
            "黛西": ["elegant", "sophisticated", "charming", "mysterious", "alluring"],
            "daisy": ["elegant", "sophisticated", "charming", "mysterious", "alluring"],
            "daisy buchanan": [
                "elegant",
                "sophisticated",
                "charming",
                "mysterious",
                "alluring",
            ],
            "奧黛麗": ["elegant", "graceful", "timeless", "sophisticated", "charming"],
            "audrey": ["elegant", "graceful", "timeless", "sophisticated", "charming"],
            "audrey hepburn": [
                "elegant",
                "graceful",
                "timeless",
                "sophisticated",
                "charming",
            ],
            "james bond": [
                "sophisticated",
                "confident",
                "suave",
                "mysterious",
                "charming",
            ],
            "gatsby": ["romantic", "ambitious", "mysterious", "elegant", "tragic"],
            "jay gatsby": ["romantic", "ambitious", "mysterious", "elegant", "tragic"],
        }

        name_lower = character_name.lower()
        traits = ["unique", "fascinating", "deep", "memorable", "distinctive"]

        for key, mapped_traits in character_traits_map.items():
            if key in name_lower:
                traits = mapped_traits
                break

        style_map = {
            "intelligent": ["academic", "sophisticated"],
            "brave": ["bold", "confident"],
            "elegant": ["refined", "classic"],
            "mysterious": ["enigmatic", "alluring"],
            "sophisticated": ["refined", "classic"],
        }

        style = ["personal", "distinctive"]
        for trait in traits:
            if trait in style_map:
                style = style_map[trait]
                break

        return {
            "traits": traits,
            "style": style,
            "analysis": f"{character_name} embodies {', '.join(traits[:3])} qualities with {', '.join(style)} style.",
        }

    # 保持其他原有方法不變...
    def enhance_fragrance_data(self, fragrance):
        """使用LLM增強香水資料，補充缺失的traits等資訊"""
        try:
            # 準備現有資訊
            name = fragrance.get("Name", "").replace(",", "").strip()
            brand = fragrance.get("Brand", "").replace(",", "").strip()
            existing_accords = fragrance.get("Accords", "").replace(",", ", ").strip()

            # 处理Notes对象
            notes_obj = fragrance.get("Notes", {})
            top_notes = notes_obj.get("Top Notes", "").replace(",", ", ").strip()
            heart_notes = notes_obj.get("Heart Notes", "").replace(",", ", ").strip()
            base_notes = notes_obj.get("Base Notes", "").replace(",", ", ").strip()

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
        return {
            "id": str(fragrance.get("_id")),
            "Name": fragrance.get("Name", "").replace(",", "").strip(),
            "Brand": fragrance.get("Brand", "").replace(",", "").strip(),
            "Accords": (
                fragrance.get("Accords", "").replace(",", ", ").strip().split(", ")
                if fragrance.get("Accords")
                else []
            ),
            "top_notes": (
                notes_obj.get("Top Notes", "").replace(",", ", ").strip().split(", ")
                if notes_obj.get("Top Notes")
                else []
            ),
            "heart_notes": (
                notes_obj.get("Heart Notes", "").replace(",", ", ").strip().split(", ")
                if notes_obj.get("Heart Notes")
                else []
            ),
            "base_notes": (
                notes_obj.get("Base Notes", "").replace(",", ", ").strip().split(", ")
                if notes_obj.get("Base Notes")
                else []
            ),
            "additional_traits": ["sophisticated", "elegant", "modern"],
            "personality_match": ["confident", "artistic", "refined"],
            "mood_description": "A sophisticated fragrance with unique character.",
            "season_suitability": ["spring", "summer"],
            "time_of_day": ["day", "evening"],
        }

    def match_fragrances(self, character_analysis, fragrances, num_recommendations=3):
        """Match fragrances based on character analysis"""
        try:
            print(f"🔄 開始處理 {len(fragrances)} 個香水...")

            enhanced_fragrances = []
            for i, fragrance in enumerate(fragrances):
                enhanced = self.enhance_fragrance_data(fragrance)
                enhanced_fragrances.append(enhanced)
                if i < len(fragrances) - 1:  # 不是最後一個
                    time.sleep(0.5)

            print(f"✅ 完成香水增強處理")

            # Format fragrance data for LLM
            fragrances_text = "\n".join(
                [
                    f"ID: {f['id']}, Name: {f['Name']}, Brand: {f['Brand']}, "
                    f"Accords: {', '.join(f['Accords'])}, "
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

            print(f"⚠️ LLM 匹配失敗，使用備用邏輯")
            return self._generate_smart_recommendations(
                enhanced_fragrances, character_analysis, num_recommendations
            )

        except Exception as e:
            print(f"❌ 香水匹配錯誤: {str(e)}")
            return self._generate_smart_recommendations(
                enhanced_fragrances if "enhanced_fragrances" in locals() else [],
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
                "rationale", "This fragrance matches the character's unique style."
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

        fragrance_traits = fragrance.get("additional_traits", []) + fragrance.get(
            "personality_match", []
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
            return f"{name}'s distinctive {', '.join(accords[:3])} blend reflects the character's unique personality."

        return f"This fragrance's distinctive character makes it an ideal match for such unique qualities."

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
            "rationale": "This fragrance's traits match the character's style.",
        }

    def generate_description(self, fragrance):
        """Generate fragrance description (同步版本)"""
        try:
            result = self.description_chain.invoke(
                {
                    "fragrance_name": fragrance["Name"],
                    "brand": fragrance["Brand"],
                    "top_notes": ", ".join(fragrance.get("top_notes", [])),
                    "heart_notes": ", ".join(fragrance.get("heart_notes", [])),
                    "base_notes": ", ".join(fragrance.get("base_notes", [])),
                    "accords": ", ".join(fragrance.get("Accords", [])),
                }
            )

            # 處理回應內容
            content = result.content if hasattr(result, "content") else str(result)
            return content.strip()

        except Exception as e:
            print(f"Description generation error: {str(e)}")
            return f"{fragrance['Name']} by {fragrance.get('Brand', 'Unknown Brand')} is a captivating fragrance that embodies elegance and sophistication. This unique scent offers a harmonious blend of carefully selected notes that create an unforgettable olfactory experience."
