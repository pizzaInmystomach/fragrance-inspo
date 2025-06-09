import json
from langchain.prompts import PromptTemplate
from .llm_config import get_balanced_model
from .prompts import CHARACTER_PROMPT, MATCHING_PROMPT, DESCRIPTION_PROMPT, TRAIT_ENHANCEMENT_PROMPT

class CharacterAnalyzer:
    """Character analyzer and fragrance matcher"""
    
    def __init__(self):
        self.llm = get_balanced_model()  # 使用平衡模型作為預設
        
        # 建立提示詞模板
        self.character_prompt = PromptTemplate(
            template=CHARACTER_PROMPT,
            input_variables=["character_name", "source_type"]
        )
        self.matching_prompt = PromptTemplate(
            template=MATCHING_PROMPT,
            input_variables=["character_analysis", "fragrances_data", "num_recommendations"]
        )
        self.description_prompt = PromptTemplate(
            template=DESCRIPTION_PROMPT,
            input_variables=["fragrance_name", "brand", "top_notes", "heart_notes", 
                            "base_notes", "accords"]
        )
        self.trait_enhancement_prompt = PromptTemplate(
            template=TRAIT_ENHANCEMENT_PROMPT,
            input_variables=["fragrance_name", "brand", "existing_accords", "notes_info"]
        )
        
        # 使用新的 LCEL 語法建立鏈
        self.character_chain = self.character_prompt | self.llm
        self.description_chain = self.description_prompt | self.llm
        self.trait_enhancement_chain = self.trait_enhancement_prompt | self.llm
        # 注意：matching_chain 會在 match_fragrances 方法中動態建立
    
    def analyze_character(self, character_name, source_type=""):
        """Analyze character traits (同步版本)"""
        try:
            # 使用新的 invoke 方法
            result = self.character_chain.invoke({
                "character_name": character_name,
                "source_type": source_type
            })
            
            # 處理回應內容
            content = result.content if hasattr(result, 'content') else str(result)
            
            # Try to parse JSON
            try:
                return json.loads(content)
            except:
                # If parsing fails, provide basic results
                return {
                    "traits": ["unique", "fascinating", "deep"],
                    "style": ["personal", "distinctive"],
                    "analysis": f"{character_name} is a character filled with unique charm and personality."
                }
        except Exception as e:
            print(f"Character analysis error: {str(e)}")
            return {
                "traits": ["unique", "fascinating", "deep"],
                "style": ["personal", "distinctive"],
                "analysis": f"{character_name} is a character filled with unique charm and personality."
            }
    
    def enhance_fragrance_data(self, fragrance):
        """使用LLM增強香水資料，補充缺失的traits等資訊"""
        try:
            # 準備現有資訊
            name = fragrance.get('Name', '').replace(',', '').strip()
            brand = fragrance.get('Brand', '').replace(',', '').strip()
            existing_accords = fragrance.get('Accords', '').replace(',', ', ').strip()
            
            # 处理Notes对象
            notes_obj = fragrance.get('Notes', {})
            top_notes = notes_obj.get('Top Notes', '').replace(',', ', ').strip()
            heart_notes = notes_obj.get('Heart Notes', '').replace(',', ', ').strip()
            base_notes = notes_obj.get('Base Notes', '').replace(',', ', ').strip()
            
            notes_info = f"Top: {top_notes}, Heart: {heart_notes}, Base: {base_notes}"
            
            # 使用LLM生成增强信息
            enhancement_result = self.trait_enhancement_chain.run(
                fragrance_name=name,
                brand=brand,
                existing_accords=existing_accords,
                notes_info=notes_info
            )
            
            try:
                enhancement_data = json.loads(enhancement_result)
            except:
                # 如果解析失败，提供基本信息
                enhancement_data = {
                    "additional_traits": ["sophisticated", "elegant", "modern"],
                    "personality_match": ["confident", "artistic", "refined"],
                    "mood_description": "A sophisticated and elegant fragrance perfect for special occasions.",
                    "season_suitability": ["spring", "summer"],
                    "time_of_day": ["evening", "night"]
                }
            
            # 合并原始数据和增强数据
            enhanced_fragrance = {
                "id": str(fragrance.get('_id')),
                "Name": name,
                "Brand": brand,
                "Accords": existing_accords.split(', ') if existing_accords else [],
                "top_notes": top_notes.split(', ') if top_notes else [],
                "heart_notes": heart_notes.split(', ') if heart_notes else [],
                "base_notes": base_notes.split(', ') if base_notes else [],
                "additional_traits": enhancement_data.get("additional_traits", []),
                "personality_match": enhancement_data.get("personality_match", []),
                "mood_description": enhancement_data.get("mood_description", ""),
                "season_suitability": enhancement_data.get("season_suitability", []),
                "time_of_day": enhancement_data.get("time_of_day", [])
            }
            
            return enhanced_fragrance
            
        except Exception as e:
            print(f"Fragrance enhancement error: {str(e)}")
            # 返回基本的增强版本
            return self._create_basic_enhanced_fragrance(fragrance)
    
    def _create_basic_enhanced_fragrance(self, fragrance):
        """创建基本的增强香水数据"""
        notes_obj = fragrance.get('Notes', {})
        return {
            "id": str(fragrance.get('_id')),
            "Name": fragrance.get('Name', '').replace(',', '').strip(),
            "Brand": fragrance.get('Brand', '').replace(',', '').strip(),
            "Accords": fragrance.get('Accords', '').replace(',', ', ').strip().split(', ') if fragrance.get('Accords') else [],
            "top_notes": notes_obj.get('Top Notes', '').replace(',', ', ').strip().split(', ') if notes_obj.get('Top Notes') else [],
            "heart_notes": notes_obj.get('Heart Notes', '').replace(',', ', ').strip().split(', ') if notes_obj.get('Heart Notes') else [],
            "base_notes": notes_obj.get('Base Notes', '').replace(',', ', ').strip().split(', ') if notes_obj.get('Base Notes') else [],
            "additional_traits": ["sophisticated", "elegant", "modern"],
            "personality_match": ["confident", "artistic", "refined"],
            "mood_description": "A sophisticated fragrance with unique character.",
            "season_suitability": ["spring", "summer"],
            "time_of_day": ["day", "evening"]
        }
    
    def match_fragrance(self, character_analysis, fragrances):
        """Match fragrance based on character analysis (同步版本)"""
        # 首先增强所有香水数据
        enhanced_fragrances = [self.enhance_fragrance_data(f) for f in fragrances]
        
        # Format fragrance data for LLM
        fragrances_text = "\n".join([
            f"ID: {f['id']}, Name: {f['Name']}, Brand: {f['Brand']}, "
            f"Accords: {', '.join(f['Accords'])}, "
            f"Additional Traits: {', '.join(f['additional_traits'])}, "
            f"Personality Match: {', '.join(f['personality_match'])}"
            for f in enhanced_fragrances
        ])
        
        try:
            result = self.matching_chain.run(
                character_analysis=json.dumps(character_analysis),
                fragrances_data=fragrances_text
            )
            
            # Try to parse result
            try:
                match_result = json.loads(content)
                fragrance_id = match_result.get("fragrance_id")
                rationale = match_result.get("rationale", "This fragrance's traits match the character's style.")
                
                # Get complete fragrance information
                matched_fragrance = next(
                    (f for f in enhanced_fragrances if f["id"] == fragrance_id),
                    enhanced_fragrances[0] if enhanced_fragrances else None
                )
                
                return {
                    "fragrance": matched_fragrance,
                    "rationale": rationale
                }
            except Exception as parse_error:
                print(f"JSON parsing error: {parse_error}")
                # Parsing failed, return the first fragrance
                return {
                    "fragrance": enhanced_fragrances[0] if enhanced_fragrances else None,
                    "rationale": "This fragrance's traits complement the character's unique style."
                }
        except Exception as e:
            print(f"Fragrance matching error: {str(e)}")
            return {
                "fragrance": enhanced_fragrances[0] if enhanced_fragrances else None,
                "rationale": "This fragrance's traits match the character's style."
            }
    
    def generate_description(self, fragrance):
        """Generate fragrance description (同步版本)"""
        try:
            result = self.description_chain.invoke({
                "fragrance_name": fragrance["Name"],
                "brand": fragrance["Brand"],
                "top_notes": ", ".join(fragrance.get("top_notes", [])),
                "heart_notes": ", ".join(fragrance.get("heart_notes", [])),
                "base_notes": ", ".join(fragrance.get("base_notes", [])),
                "accords": ", ".join(fragrance.get("Accords", []))
            })
            
            # 處理回應內容
            content = result.content if hasattr(result, 'content') else str(result)
            return content.strip()
            
        except Exception as e:
            print(f"Description generation error: {str(e)}")
            return f"{fragrance['Name']} by {fragrance.get('Brand', 'Unknown Brand')} is a captivating fragrance that embodies elegance and sophistication. This unique scent offers a harmonious blend of carefully selected notes that create an unforgettable olfactory experience."