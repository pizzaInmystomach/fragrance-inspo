# Character analysis prompt
CHARACTER_PROMPT = """
Please analyze the following character or celebrity's personality traits, style characteristics, and overall vibe:
Character/Celebrity name: {character_name}
Character source: {source_type}

Please provide:
1. 5-7 key personality traits
2. 3-5 style characteristics
3. A brief character analysis description (50-100 words)

Format as JSON:
{{
  "traits": ["trait1", "trait2", "trait3", "trait4", "trait5"],
  "style": ["style1", "style2", "style3"],
  "analysis": "Character analysis description..."
}}
"""

# Fragrance matching prompt
MATCHING_PROMPT = """
Based on the following character analysis, select the top {num_recommendations} most matching fragrances from the provided list.

Character analysis: {character_analysis}

Fragrance list:
{fragrances_data}

Please choose the {num_recommendations} fragrance IDs that best suit this character, ranked from most suitable to least suitable.
Consider the character's personality traits, style, and overall vibe when making your selections.
Provide different reasons for each recommendation to show variety.

Format as JSON:
{{
  "recommendations": [
    {{
      "fragrance_id": "first choice fragrance ID",
      "rationale": "Why this fragrance is the best match (2-3 sentences)"
    }},
    {{
      "fragrance_id": "second choice fragrance ID", 
      "rationale": "Why this fragrance is the second best match (2-3 sentences)"
    }},
    {{
      "fragrance_id": "third choice fragrance ID",
      "rationale": "Why this fragrance is the third best match (2-3 sentences)"
    }}
  ]
}}
"""

# Fragrance description prompt
DESCRIPTION_PROMPT = """
Please create a vivid description of the following fragrance's scent experience:
   
Fragrance name: {fragrance_name}
Brand: {brand}
Top notes: {top_notes}
Heart/Middle notes: {heart_notes}
Base notes: {base_notes}
Main accords: {accords}
   
Provide a 100-150 word vivid description that captures:
1. The opening impression (top notes)
2. The heart development (middle notes)  
3. The lasting base (base notes)
4. The overall mood and feeling of the fragrance

Write in an engaging, poetic style that helps readers imagine the scent experience.
"""

# New prompt for enhancing fragrance data with LLM
TRAIT_ENHANCEMENT_PROMPT = """
Based on the fragrance information provided, please analyze and provide additional characteristics that would help match this fragrance to different personality types.

Fragrance name: {fragrance_name}
Brand: {brand}
Existing accords: {existing_accords}
Notes information: {notes_info}

Please provide:
1. 3-5 additional personality traits this fragrance would appeal to
2. 3-5 personality types that would match this fragrance
3. A brief mood/feeling description (1-2 sentences)
4. Suitable seasons (spring, summer, autumn, winter)
5. Best time of day (morning, afternoon, evening, night)

Format as JSON:
{{
  "additional_traits": ["trait1", "trait2", "trait3"],
  "personality_match": ["personality1", "personality2", "personality3"],
  "mood_description": "Brief description of the mood and feeling this fragrance evokes",
  "season_suitability": ["season1", "season2"],
  "time_of_day": ["time1", "time2"]
}}
"""