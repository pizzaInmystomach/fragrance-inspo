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
Based on the following character analysis, select the most matching fragrance from the provided list.

Character analysis: {character_analysis}

Fragrance list:
{fragrances_data}

Please choose the fragrance ID that best suits this character and explain why.
Format as JSON:
{{
  "fragrance_id": "selected fragrance ID",
  "rationale": "Why this fragrance suits the character"
}}
"""

# Fragrance description prompt
DESCRIPTION_PROMPT = """
Please create a vivid description of the following fragrance's scent experience:
   
Fragrance name: {fragrance_name}
Top notes: {top_notes}
Middle notes: {middle_notes}
Base notes: {base_notes}
Main accords: {main_accords}
   
Provide a 100-150 word vivid description, including the progression through top, middle, and base notes and the overall impression.
"""