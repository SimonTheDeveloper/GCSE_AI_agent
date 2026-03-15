"""LLM prompts for GCSE help generation."""

import json
from typing import Any, Dict


def get_system_prompt() -> str:
    """Get the system prompt for the GCSE tutor assistant.
    
    Returns:
        System prompt string instructing the LLM on behavior and output format
    """
    return (
        "You are a GCSE tutor assistant. Return ONLY valid JSON that conforms to the requested structure. "
        "Use UK tone (en-GB) and age-appropriate wording for Year 9 unless otherwise specified. "
        "Do not include markdown fences. Do not include commentary."
    )


def get_user_prompt(base_structure: Dict[str, Any]) -> str:
    """Get the user prompt for generating GCSE help content.
    
    Args:
        base_structure: The base GCSE help structure to populate
        
    Returns:
        User prompt string with instructions and the base structure
    """
    return (
        "Fill in and complete the JSON object below. Keep the same keys. Replace placeholder empty strings/arrays with real content. "
        "Populate analysis.topics, analysis.prerequisites, analysis.common_mistakes appropriately. "
        "Populate help.tiers with progressive help: nudge (1-2 lines), hint (bullets), steps (numbered bullets), worked (math lines), teachback (why it works). "
        "Use help.formulas_used only if relevant. Include a check_your_answer with substitution check. Add 2-3 practice questions with final answers only. "
        "Return strictly valid JSON.\n\n"
        + json.dumps(base_structure, ensure_ascii=False)
    )
