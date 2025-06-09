INPUT_PARSING_PROMPT = """
You are a JSON API. You MUST respond with ONLY valid JSON, no explanations, no code, no markdown.

Task: Extract character information from user input for fragrance recommendation.

User input: "{user_input}"

Return ONLY the JSON object below, nothing else:

{{
  "status": "success" or "need_clarification" or "invalid",
  "character_name": "extracted character name" or null,
  "source": "detected source/franchise" or null,
  "intent": "description of what user wants",
  "message": "response message to user"
}}

Rules:
1. If user mentions wanting to smell like a character, extract the character name
2. If user mentions a specific character, extract it even without "smell like"
3. If input is greeting/casual chat, set status to "invalid" and ask for character info
4. If character is unclear, set status to "need_clarification" and ask for more details
5. If character is clear, set status to "success"

Examples:
- "I want to smell like Harry Potter" → success, character_name: "Harry Potter"
- "Hermione Granger" → success, character_name: "Hermione Granger"  
- "What fragrance would Daisy Buchanan wear" → success, character_name: "Daisy Buchanan"
- "Hello" → invalid, ask for character information
- "Someone brave" → need_clarification, ask for specific character name
"""

# Character analysis prompt - 改進版
CHARACTER_PROMPT = """
You are a character analysis expert. Analyze the following character's personality and style.

Character/Celebrity: {character_name}
Source: {source_type}

Provide a detailed analysis focusing on:
1. Key personality traits (5-7 traits)
2. Style characteristics (3-5 characteristics)  
3. Brief character analysis (50-100 words)

IMPORTANT: Respond ONLY the valid JSON in this exact format:

{{
  "traits": ["trait1", "trait2", "trait3", "trait4", "trait5"],
  "style": ["style1", "style2", "style3"],
  "analysis": "Character analysis description here..."
}}

Do not include any text before or after the JSON. Only return the JSON object.
"""

# Fragrance matching prompt - 改進版
MATCHING_PROMPT = """
You are a fragrance matching expert. Based on the character analysis, select the top {num_recommendations} most suitable fragrances.

Character Analysis: {character_analysis}

Available Fragrances:
{fragrances_data}

Select the {num_recommendations} best matching fragrances and provide unique, personalized reasons for each recommendation.

IMPORTANT: Respond ONLY with valid JSON in this exact format:

{{
  "recommendations": [
    {{
      "fragrance_id": "actual_fragrance_id_from_list",
      "rationale": "Specific reason why this fragrance matches the character's personality and style (2-3 sentences)"
    }},
    {{
      "fragrance_id": "actual_fragrance_id_from_list",
      "rationale": "Different reason focusing on other aspects of the character (2-3 sentences)"
    }},
    {{
      "fragrance_id": "actual_fragrance_id_from_list", 
      "rationale": "Third unique reason highlighting different matching elements (2-3 sentences)"
    }}
  ]
}}

Do not include any text before or after the JSON. Only return the JSON object.
"""

# Fragrance description prompt - 保持不變
DESCRIPTION_PROMPT = """
Create a vivid, engaging description of this fragrance's scent experience:
   
Fragrance: {fragrance_name} by {brand}
Top notes: {top_notes}
Heart/Middle notes: {heart_notes}
Base notes: {base_notes}
Main accords: {accords}
   
Write a 100-150 word poetic description that captures:
1. The opening impression (top notes)
2. The heart development (middle notes)  
3. The lasting base (base notes)
4. The overall mood and feeling

Use engaging, sensory language that helps readers imagine the scent experience.
"""

# Trait enhancement prompt - 改進版
TRAIT_ENHANCEMENT_PROMPT = """
You are a fragrance personality expert. Analyze this fragrance and provide personality insights.

Fragrance: {fragrance_name} by {brand}
Existing accords: {existing_accords}
Notes: {notes_info}

Provide personality and style insights for this fragrance.

IMPORTANT: Respond ONLY with valid JSON in this exact format:

{{
  "additional_traits": ["trait1", "trait2", "trait3"],
  "personality_match": ["personality1", "personality2", "personality3"],
  "mood_description": "Brief description of the mood this fragrance evokes",
  "season_suitability": ["season1", "season2"],
  "time_of_day": ["time1", "time2"]
}}

Do not include any text before or after the JSON. Only return the JSON object.
"""