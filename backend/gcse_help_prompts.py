"""LLM prompts for GCSE help generation.

System and user prompts are kept as module-level constants so they can be
seeded into DynamoDB on first run. The generator loads the live version from
DB at startup; these constants are the v1 seed values only.
"""

INGESTION_SYSTEM_PROMPT = (
    "You are a GCSE tutor assistant. Return ONLY valid JSON that conforms to the requested structure. "
    "Use UK tone (en-GB) and age-appropriate wording for Year 9 unless otherwise specified. "
    "Do not include markdown fences. Do not include commentary."
)

# {{BASE_STRUCTURE}} is replaced at runtime with the JSON scaffold for the problem.
INGESTION_USER_PROMPT_TEMPLATE = (
    "Fill in and complete the JSON object below. Keep the same keys. Replace placeholder empty strings/arrays with real content. "
    "Populate analysis.topics, analysis.prerequisites, analysis.common_mistakes appropriately. "
    "Populate help.tiers with progressive help: nudge (1-2 lines), hint (bullets), steps (numbered bullets), worked (math lines), teachback (why it works). "
    "Use help.formulas_used only if relevant. Include a check_your_answer with substitution check. Add 2-3 practice questions with final answers only. "
    "Return strictly valid JSON.\n\n"
    "{{BASE_STRUCTURE}}"
)


def get_system_prompt() -> str:
    return INGESTION_SYSTEM_PROMPT


def get_user_prompt_template() -> str:
    return INGESTION_USER_PROMPT_TEMPLATE


def render_user_prompt(template: str, base_structure_json: str) -> str:
    return template.replace("{{BASE_STRUCTURE}}", base_structure_json)


def seed_ingestion_prompt_if_missing() -> bool:
    """Write the v1 ingestion prompt to DynamoDB if it hasn't been seeded yet.

    Returns True if a seed was written, False if it already existed.
    """
    import db
    if db.get_prompt_active("ingestion") is not None:
        return False
    db.put_prompt_version(
        "ingestion",
        system_prompt=INGESTION_SYSTEM_PROMPT,
        user_prompt_template=INGESTION_USER_PROMPT_TEMPLATE,
        created_by="seed",
        notes="Initial seed from gcse_help_prompts.py",
    )
    return True
