import json
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from .llm_config import CHARACTER_MODEL
from .prompts import CHARACTER_PROMPT, MATCHING_PROMPT, DESCRIPTION_PROMPT

class CharacterAnalyzer:
    """Character analyzer and fragrance matcher"""
    
    def __init__(self):
        self.llm = CHARACTER_MODEL
        self.character_prompt = PromptTemplate(
            template=CHARACTER_PROMPT,
            input_variables=["character_name", "source_type"]
        )
        self.matching_prompt = PromptTemplate(
            template=MATCHING_PROMPT,
            input_variables=["character_analysis", "fragrances_data"]
        )
        self.description_prompt = PromptTemplate(
            template=DESCRIPTION_PROMPT,
            input_variables=["fragrance_name", "top_notes", "middle_notes", 
                            "base_notes", "main_accords"]
        )
        
        # Build chains
        self.character_chain = LLMChain(llm=self.llm, prompt=self.character_prompt)
        self.matching_chain = LLMChain(llm=self.llm, prompt=self.matching_prompt)
        self.description_chain = LLMChain(llm=self.llm, prompt=self.description_prompt)
    
    async def analyze_character(self, character_name, source_type=""):
        """Analyze character traits"""
        try:
            result = await self.character_chain.arun(
                character_name=character_name,
                source_type=source_type
            )
            
            # Try to parse JSON
            try:
                return json.loads(result)
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
    
    async def match_fragrance(self, character_analysis, fragrances):
        """Match fragrance based on character analysis"""
        # Format fragrance data
        fragrances_text = "\n".join([
            f"ID: {f['id']}, Name: {f['name']}, Brand: {f['brand']}, " 
            f"Traits: {', '.join(f['traits'])}" 
            for f in fragrances
        ])
        
        try:
            result = await self.matching_chain.arun(
                character_analysis=json.dumps(character_analysis),
                fragrances_data=fragrances_text
            )
            
            # Try to parse result
            try:
                match_result = json.loads(result)
                fragrance_id = match_result.get("fragrance_id")
                rationale = match_result.get("rationale", "This fragrance's traits match the character's style.")
                
                # Get complete fragrance information
                matched_fragrance = next((f for f in fragrances if f["id"] == fragrance_id), fragrances[0])
                
                return {
                    "fragrance": matched_fragrance,
                    "rationale": rationale
                }
            except:
                # Parsing failed, return the first fragrance
                return {
                    "fragrance": fragrances[0],
                    "rationale": "This fragrance's traits match the character's style."
                }
        except Exception as e:
            print(f"Fragrance matching error: {str(e)}")
            return {
                "fragrance": fragrances[0],
                "rationale": "This fragrance's traits match the character's style."
            }
    
    async def generate_description(self, fragrance):
        """Generate fragrance description"""
        try:
            description = await self.description_chain.arun(
                fragrance_name=fragrance["name"],
                top_notes=", ".join(fragrance.get("top_notes", [])),
                middle_notes=", ".join(fragrance.get("middle_notes", [])),
                base_notes=", ".join(fragrance.get("base_notes", [])),
                main_accords=", ".join(fragrance.get("main_accords", []))
            )
            
            return description.strip()
        except Exception as e:
            print(f"Description generation error: {str(e)}")
            return f"{fragrance['name']} is a fragrance by {fragrance['brand']} with a unique progression of top, middle, and base notes."