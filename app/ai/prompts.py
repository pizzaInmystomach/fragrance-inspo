INPUT_PARSING_PROMPT = """
You are a JSON API. You MUST respond with ONLY valid JSON, no explanations, no code, no markdown.

Task: Determine whether the user provided a usable scene, environment, mood, or scent brief for fragrance recommendation.

User input: "{user_input}"

Return ONLY the JSON object below, nothing else:

{{
  "status": "success" or "need_clarification" or "invalid",
  "scene_prompt": "cleaned scene/environment/scent brief" or null,
  "intent": "description of what user wants",
  "message": "response message to user"
}}

Rules:
1. If the user describes a setting, environment, occasion, mood, sensory atmosphere, fragrance family, or notes, set status to "success".
2. Preserve concrete scent clues such as woody, earthy, old books, rain, library, citrus, floral, smoky, clean, cozy, etc.
3. If the input is only a greeting/casual chat, set status to "invalid" and ask for a scene, environment, or scent mood.
4. If the input is too vague, set status to "need_clarification" and ask for more sensory or environmental details.
5. Do not extract a fictional character. This API is for scene and environment analysis.

Examples:
- "Rainy library" -> success, scene_prompt: "Rainy library"
- "I am looking for a woody fragrance with notes of earth and old book pages" -> success
- "Something cozy for a winter cabin" -> success
- "Hello" -> invalid
- "Something nice" -> need_clarification
"""

# Scene analysis prompt
SCENE_PROMPT = """
You are a fragrance atmosphere analyst. Analyze the following scene, environment, mood, or scent brief.

Scene / Environment Prompt: {scene_prompt}

Provide a detailed analysis focusing on:
1. Key atmospheric scent traits (5-7 traits)
2. Style characteristics (3-5 characteristics)
3. Brief scene analysis (50-100 words) that explains the desired fragrance mood

IMPORTANT: Respond ONLY the valid JSON in this exact format:

{{
  "traits": ["trait1", "trait2", "trait3", "trait4", "trait5"],
  "style": ["style1", "style2", "style3"],
  "analysis": "Character analysis description here..."
}}

Do not include any text before or after the JSON. Only return the JSON object.
"""

# Backward-compatible alias for older imports.
CHARACTER_PROMPT = SCENE_PROMPT

# Fragrance matching prompt - 改進版
MATCHING_PROMPT = """
You are a fragrance matching expert. Based on the scene/environment analysis, select the top {num_recommendations} most suitable fragrances.

Scene / Environment Analysis: {character_analysis}

Available Fragrances:
{fragrances_data}

Select the {num_recommendations} best matching fragrances and provide unique, sensory reasons for each recommendation.

IMPORTANT: Respond ONLY with valid JSON in this exact format:

{{
  "recommendations": [
    {{
      "fragrance_id": "actual_fragrance_id_from_list",
      "rationale": "Specific reason why this fragrance matches the scene, environment, mood, and scent brief (2-3 sentences)"
    }},
    {{
      "fragrance_id": "actual_fragrance_id_from_list",
      "rationale": "Different reason focusing on other atmospheric or olfactory aspects of the prompt (2-3 sentences)"
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
