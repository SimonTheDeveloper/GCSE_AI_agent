"""Markup-feedback evaluation for student submissions.

Phase 1 of the rebuilt evaluation engine. Given a stored Problem and a
freeform student submission, this module:

1. Tries cheap-first matching (exact normalised match against the canonical
   final answer). Returns immediately if it hits — no LLM call.
2. Otherwise calls an LLM with the admin-managed `evaluation` prompt and
   asks it to mark up the submission as a list of segments, each tagged
   `correct` / `incomplete` / `wrong` / `unclear`.
3. Validates that the segments concatenate back to the original submission
   character-for-character. On mismatch, falls back to a plain-prose shape
   so the frontend never renders misaligned markup.

Kept separate from `gcse_help_generator` to avoid coupling the at-creation
generator workflow with the per-submission evaluation workflow — they have
different latency profiles and different prompts.
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ── Cheap-first matching ────────────────────────────────────────────────────


def _normalise(text: str) -> str:
    """Conservative normalisation for cheap-path string comparison.

    Lowercases, strips whitespace, and removes all internal whitespace so
    that "x = 6" matches "x=6" and "X = 6". Mirrors the existing
    `_normalise_answer` in main.py — kept in lockstep on purpose.
    """
    return (text or "").strip().lower().replace(" ", "")


def _final_answer_candidates(ai_response: Dict[str, Any]) -> List[str]:
    """Pull every string we'd be willing to recognise as "the answer".

    Prefers the v3 shape (top-level `milestone_answers`, last entry is the
    final answer). Falls back to the v2 shape (`steps[-1].expected_answer`)
    so cached pre-v3 problems keep working through the cache turnover.
    """
    candidates: List[str] = []

    # v3: top-level milestone_answers
    milestones = ai_response.get("milestone_answers")
    if isinstance(milestones, list) and milestones:
        last = milestones[-1]
        if isinstance(last, str) and last.strip():
            candidates.append(last)
            return candidates  # v3 is authoritative when present

    # v2 fallback: last step's expected_answer
    steps = ai_response.get("steps") or []
    if isinstance(steps, list) and steps:
        last = steps[-1]
        if isinstance(last, dict):
            ea = last.get("expected_answer")
            if isinstance(ea, str) and ea.strip():
                candidates.append(ea)
    return candidates


def _build_simpler_payload(ai_response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Synthesise a v3-shaped sub-payload from the simpler_version field.

    Returns a dict with `full_solution` and `milestone_answers` populated
    from the simpler problem, suitable for re-running the existing pipeline
    against. Returns None when simpler_version is absent or malformed.

    `milestone_answers` for the simpler version isn't stored separately in
    the schema — the simpler problem is short by design. We use the whole
    solution string as the single milestone, which lets the cheap-path
    catch full-answer submissions but won't catch intermediate ones. That's
    acceptable because the simpler version is meant to be a quick warm-up.
    """
    sv = ai_response.get("simpler_version")
    if not isinstance(sv, dict):
        return None
    solution = sv.get("solution")
    if not isinstance(solution, str) or not solution.strip():
        return None
    return {
        "full_solution": solution,
        "milestone_answers": [solution.strip()],
        "normalised_form": sv.get("question") or "",
        "opening_prompt": sv.get("opening_prompt") or "",
    }


def cheap_match_final_answer(submission: str, ai_response: Dict[str, Any]) -> bool:
    """Return True if the submission contains the canonical final answer.

    Phase 1 keeps this conservative: exact normalised match. Substring
    matching is tempting but creates false positives (e.g. "x=6" matches
    inside "x=64"). We can loosen this once the markup path is proven and
    we have data on the false-negative rate.
    """
    normalised_submission = _normalise(submission)
    if not normalised_submission:
        return False
    for candidate in _final_answer_candidates(ai_response):
        if _normalise(candidate) == normalised_submission:
            return True
    return False


# ── LLM evaluation ──────────────────────────────────────────────────────────


@dataclass
class EvaluationOutcome:
    """Outcome of an evaluator call.

    On a cheap-path final-answer hit: is_correct=True, segments=[],
    prose_feedback=None, next_prompt=None.

    On a successful LLM call with valid markup: is_correct=False,
    segments populated, prose_feedback=None. next_prompt is set in
    guided mode (and only when the LLM produced one); None in free mode.

    On an LLM call where the markup didn't validate (segments don't
    reconstruct the original submission, or the JSON was malformed):
    is_correct=False, segments=[], prose_feedback set to a short note the
    frontend can render in plain prose. next_prompt is None.
    """
    is_correct: bool
    segments: List[Dict[str, Any]]
    prose_feedback: Optional[str]
    next_prompt: Optional[str] = None


class EvaluatorError(RuntimeError):
    pass


def _load_active_prompt() -> tuple[str, str]:
    """Load the active evaluation prompt's system + user template from DynamoDB.

    Imported inside the function so this module can be imported without a
    DB connection (e.g. for unit tests that stub the LLM call directly).
    """
    import db
    active = db.get_prompt_active("evaluation")
    if not active:
        raise EvaluatorError(
            "evaluation prompt not seeded — restart the server or seed via admin UI"
        )
    version = int(active["version"])
    record = db.get_prompt_version("evaluation", version)
    if not record:
        raise EvaluatorError(f"evaluation prompt version {version} missing from DB")
    return record["systemPrompt"], record["userPromptTemplate"]


def _segments_concatenate_to(segments: List[Dict[str, Any]], original: str) -> bool:
    """Markup integrity check.

    Concatenates segment.text in order and returns True iff the result
    equals the original submission character-for-character. Used to gate
    whether we render markup or fall back to prose.
    """
    if not isinstance(segments, list):
        return False
    pieces: List[str] = []
    for seg in segments:
        if not isinstance(seg, dict):
            return False
        text = seg.get("text")
        if not isinstance(text, str):
            return False
        pieces.append(text)
    return "".join(pieces) == original


def _reconstruct_with_whitespace(
    segments: List[Dict[str, Any]],
    original: str,
) -> Optional[List[Dict[str, Any]]]:
    """Repair segments where the LLM dropped pure-whitespace runs.

    Walks the original string left-to-right and locates each segment's text
    in turn. Any gap between consecutive segments that is *purely
    whitespace* in the original is re-inserted as a standalone "correct"
    segment with a null comment. Anything more substantial than whitespace
    means the LLM rewrote the student's text and we cannot safely render
    markup — return None to fall back to prose.

    This handles the common LLM failure mode where the model dropped a
    line break between two lines of working but otherwise kept the
    student's text verbatim.
    """
    if not isinstance(segments, list) or not segments:
        return None

    patched: List[Dict[str, Any]] = []
    pos = 0
    for seg in segments:
        text = seg.get("text") if isinstance(seg, dict) else None
        if not isinstance(text, str) or text == "":
            return None

        idx = original.find(text, pos)
        if idx == -1:
            # Segment text doesn't appear in the remaining original at all
            # — the LLM rewrote it, not just dropped whitespace.
            return None

        if idx > pos:
            gap = original[pos:idx]
            if gap.strip() != "":
                # Non-whitespace content was dropped — can't safely repair.
                return None
            patched.append({"text": gap, "status": "correct", "comment": None})

        patched.append(seg)
        pos = idx + len(text)

    if pos < len(original):
        tail = original[pos:]
        if tail.strip() != "":
            return None
        patched.append({"text": tail, "status": "correct", "comment": None})

    return patched


_VALID_STATUSES = {"correct", "incomplete", "wrong", "unclear"}

# Phrases that strongly indicate the comment is correcting a mistake. If the
# LLM tagged a segment 'correct' or 'incomplete' but its comment contains one
# of these, the model has named a mistake without owning it in the status —
# we promote the status to 'wrong'. See known-issues/2026-05-02-evaluator-
# under-tags-wrong.md for context. The list is deliberately small to keep
# false positives low: each phrase is unambiguously corrective in tutor-style
# feedback.
_WRONG_SIGNAL_PHRASES = (
    "should be",
    "instead of",
    "incorrect",
)


def _comment_indicates_wrong(comment: Optional[str]) -> bool:
    if not comment:
        return False
    lowered = comment.lower()
    return any(phrase in lowered for phrase in _WRONG_SIGNAL_PHRASES)


def _normalise_segments(raw_segments: Any) -> List[Dict[str, Any]]:
    """Coerce raw LLM output into the exact shape the API returns.

    Accepts a list of dicts; for each, keeps only the three fields we
    expose, coerces status to a known value, converts missing/empty
    comments to None, and promotes 'correct'/'incomplete' segments to
    'wrong' when the comment clearly names a mistake.
    """
    if not isinstance(raw_segments, list):
        return []
    cleaned: List[Dict[str, Any]] = []
    for seg in raw_segments:
        if not isinstance(seg, dict):
            return []
        text = seg.get("text")
        if not isinstance(text, str):
            return []
        status = seg.get("status")
        if not isinstance(status, str) or status not in _VALID_STATUSES:
            # Treat unknown status as 'unclear' rather than rejecting the
            # whole response — the LLM occasionally invents adjacent labels.
            status = "unclear"
        comment = seg.get("comment")
        if not isinstance(comment, str) or not comment.strip():
            comment = None

        # Status repair: works around model leniency bias.
        if status in ("correct", "incomplete") and _comment_indicates_wrong(comment):
            logger.info(
                "evaluate_submission: promoting status %r to 'wrong' based on comment",
                status,
            )
            status = "wrong"

        cleaned.append({"text": text, "status": status, "comment": comment})
    return cleaned


def _call_llm(*, system_prompt: str, user_prompt: str, model: str) -> str:
    """Single LLM call returning the raw response content as a string.

    Mirrors the OpenAI client usage in `gcse_help_generator` and the admin
    try-prompt route — kept inline rather than refactored out because we
    only have two callers and the signatures differ.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EvaluatorError("OPENAI_API_KEY not set")
    import openai  # type: ignore
    client = openai.OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=2000,
    )
    return resp.choices[0].message.content or "{}"


def evaluate_submission(
    *,
    submission: str,
    ai_response: Dict[str, Any],
    question: str,
    mode: str = "free",
    target: str = "main",
    model: Optional[str] = None,
) -> EvaluationOutcome:
    """Run the full evaluation pipeline for one submission.

    Cheap path → LLM path → markup-validate → prose fallback.
    `mode` is "free" or "guided" — controls whether the LLM is asked
    to suggest a next_prompt for the student.
    `target` is "main" (default) or "simpler" — when "simpler", the canonical
    solution and milestones are taken from `ai_response.simpler_version`.
    """
    # If target is simpler, swap in the simpler-version payload as the
    # canonical solution + milestones for this evaluation. The rest of the
    # pipeline doesn't need to know it's a simpler version.
    if target == "simpler":
        simpler = _build_simpler_payload(ai_response)
        if simpler is None:
            return EvaluationOutcome(
                is_correct=False,
                segments=[],
                prose_feedback=(
                    "This problem doesn't have a simpler version available. "
                    "Try the original instead."
                ),
            )
        ai_response = simpler
        question = simpler.get("normalised_form") or question

    # 1. Cheap-first: final-answer match
    if cheap_match_final_answer(submission, ai_response):
        return EvaluationOutcome(
            is_correct=True, segments=[], prose_feedback=None, next_prompt=None,
        )

    # 2. LLM path
    canonical_solution = ai_response.get("full_solution") or ""
    if not isinstance(canonical_solution, str) or not canonical_solution.strip():
        # Without a canonical solution we have no grounding for the LLM.
        # Fail safe: prose fallback so the student gets *something*.
        return EvaluationOutcome(
            is_correct=False,
            segments=[],
            prose_feedback=(
                "I can see your working but I don't have a reference solution "
                "for this problem yet, so I can't give detailed feedback. "
                "Please flag this to your teacher."
            ),
        )

    try:
        system_prompt, user_template = _load_active_prompt()
    except EvaluatorError:
        logger.exception("evaluate_submission: prompt load failed")
        return EvaluationOutcome(
            is_correct=False,
            segments=[],
            prose_feedback="The feedback service isn't fully set up yet. Please try again shortly.",
        )

    from gcse_help_prompts import render_evaluation_prompt
    user_prompt = render_evaluation_prompt(
        user_template,
        question=question,
        canonical_solution=canonical_solution,
        submission=submission,
        mode=mode,
    )

    try:
        raw = _call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        )
    except Exception:
        logger.exception("evaluate_submission: LLM call failed")
        return EvaluationOutcome(
            is_correct=False,
            segments=[],
            prose_feedback="I couldn't reach the feedback service just now — please try again in a moment.",
        )

    # 3. Parse + validate
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("evaluate_submission: non-JSON LLM response")
        return EvaluationOutcome(
            is_correct=False,
            segments=[],
            prose_feedback="I couldn't read the feedback service's response. Please try again.",
        )

    raw_segments = parsed.get("feedback_segments") if isinstance(parsed, dict) else None
    cleaned = _normalise_segments(raw_segments)

    if not cleaned:
        _log_validation_failure(
            reason="empty_or_invalid_segments",
            raw_response=raw,
            submission=submission,
        )
        return _prose_fallback_from(parsed)

    if not _segments_concatenate_to(cleaned, submission):
        # Try reconstructing missing whitespace before giving up. The most
        # common LLM failure mode here is dropping a line break between two
        # lines of working — we can recover those without losing fidelity.
        reconstructed = _reconstruct_with_whitespace(cleaned, submission)
        if reconstructed is not None:
            logger.info(
                "evaluate_submission: reconstructed missing whitespace into segments"
            )
            cleaned = reconstructed
        else:
            _log_validation_failure(
                reason="segments_dont_reconstruct",
                raw_response=raw,
                submission=submission,
            )
            return _prose_fallback_from(parsed)

    # Pull the next_prompt out of the LLM response, but only honour it in
    # guided mode. In free mode the system prompt forbids it; even if the
    # LLM produces one anyway, drop it.
    next_prompt: Optional[str] = None
    if mode == "guided" and isinstance(parsed, dict):
        candidate = parsed.get("next_prompt")
        if isinstance(candidate, str) and candidate.strip():
            next_prompt = candidate.strip()

    return EvaluationOutcome(
        is_correct=False,
        segments=cleaned,
        prose_feedback=None,
        next_prompt=next_prompt,
    )


def _log_validation_failure(*, reason: str, raw_response: str, submission: str) -> None:
    """Log enough detail to diagnose why markup validation failed.

    The raw response and submission are truncated to 500 chars each to keep
    log lines manageable, but this is meant to be the primary signal for
    fixing the multi-line known-issue. See known-issues/2026-05-02-evaluator-
    multiline-prose-fallback.md for what to look for in the log output.
    """
    truncated_raw = raw_response if len(raw_response) <= 500 else raw_response[:500] + "…"
    truncated_sub = submission if len(submission) <= 500 else submission[:500] + "…"
    logger.warning(
        "evaluate_submission: markup validation failed reason=%s submission=%r raw_response=%r",
        reason,
        truncated_sub,
        truncated_raw,
    )


def _prose_fallback_from(parsed: Any) -> EvaluationOutcome:
    """Build a prose-fallback EvaluationOutcome from the parsed LLM response.

    Uses any prose-shaped field the LLM happened to include; otherwise
    emits a generic note the frontend can render.
    """
    fallback: Optional[str] = None
    if isinstance(parsed, dict):
        cand = parsed.get("prose_feedback") or parsed.get("comment")
        if isinstance(cand, str) and cand.strip():
            fallback = cand.strip()
    if not fallback:
        fallback = (
            "I had a look at your working but the feedback didn't come back "
            "in a shape I can render reliably. Try resubmitting — or simplify "
            "the working a little and I'll have another go."
        )
    return EvaluationOutcome(
        is_correct=False,
        segments=[],
        prose_feedback=fallback,
    )
