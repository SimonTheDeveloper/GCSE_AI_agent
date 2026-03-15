"""Template structure for GCSE help JSON responses."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import hashlib


def _now_iso() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def create_gcse_help_base_structure(
    *,
    normalized_text: str,
    raw_text: str,
    schema_version: str,
    uid: Optional[str] = None,
    year_group: Optional[int] = 9,
    tier: str = "unknown",
    desired_help_level: str = "auto",
    origin_type: str = "student_homework",
    origin_label: str = "Student homework",
) -> Dict[str, Any]:
    """Create the base structure for a GCSE help response.
    
    Args:
        normalized_text: Normalized exercise text for consistent processing
        raw_text: Original exercise text as provided by user
        schema_version: Version of the GCSE help schema
        uid: Optional student user ID
        year_group: Student's year group (default: 9)
        tier: GCSE tier (foundation/higher/unknown)
        desired_help_level: Requested help level (auto/nudge/hint/etc)
        origin_type: Type of exercise origin (default: student_homework)
        origin_label: Human-readable label for origin
        
    Returns:
        Dictionary containing the base GCSE help structure
    """
    request_id = f"req_{hashlib.sha1((normalized_text + _now_iso()).encode()).hexdigest()[:12]}"
    exercise_id = f"ex_{hashlib.sha1(normalized_text.encode()).hexdigest()[:12]}"

    return {
        "schema_version": schema_version,
        "request": {
            "id": request_id,
            "created_at": _now_iso(),
            "locale": "en-GB",
            "student_context": {
                "uid": uid,
                "year_group": year_group,
                "tier": tier,
                "desired_help_level": desired_help_level,
                "what_ive_tried": "",
            },
            "input": {"modality": "typed_text", "typed_text": {"text": normalized_text}},
        },
        "exercise": {
            "exercise_id": exercise_id,
            "origin": {"type": origin_type, "label": origin_label, "created_at": _now_iso()},
            "prompt": {
                "normalized_text": normalized_text,
                "raw_text": raw_text,
                "attachments": [],
            },
            "extraction": {"status": "ok", "confidence": 1, "ambiguities": []},
        },
        "analysis": {
            "subject": "maths",
            "topics": [],
            "difficulty": {"gcse_tier_hint": "unknown", "confidence": 0.5},
            "prerequisites": [],
            "common_mistakes": [],
        },
        "help": {
            "recommended_start": "nudge",
            "tiers": {
                "nudge": {"title": "", "content": [{"type": "plain", "text": ""}]},
                "hint": {"title": "", "content": [{"type": "plain", "text": ""}]},
                "steps": {"title": "", "content": [{"type": "plain", "text": "", "expectedAnswer": ""}]},
                "worked": {"title": "", "content": [{"type": "plain", "text": ""}]},
                "teachback": {"title": "", "content": [{"type": "plain", "text": ""}]},
            },
            "formulas_used": [],
            "check_your_answer": {"instruction": "", "worked_check": ""},
            "practice": [],
        },
    }
