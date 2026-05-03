"""Tests for the /homework/evaluate endpoint and the evaluator pipeline.

These exercise the cheap-path → LLM-path → markup-validation flow without
touching DynamoDB or OpenAI: db helpers and the LLM call are stubbed out.
"""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import db
import gcse_evaluator
import main


# ── Fixtures ────────────────────────────────────────────────────────────────


SAMPLE_AI_RESPONSE = {
    "normalised_form": "Differentiate y = (3x^2 + 2)^5 with respect to x",
    "full_solution": (
        "Let u = 3x^2 + 2. Then y = u^5. By the chain rule, "
        "dy/dx = 5u^4 * du/dx. du/dx = 6x. So dy/dx = 30x(3x^2 + 2)^4."
    ),
    "steps": [
        {"step_number": 1, "expected_answer": "y = u^5 with u = 3x^2 + 2"},
        {"step_number": 2, "expected_answer": "dy/dx = 5(3x^2 + 2)^4 * du/dx"},
        {"step_number": 3, "expected_answer": "du/dx = 6x"},
        {"step_number": 4, "expected_answer": "dy/dx = 30x(3x^2 + 2)^4"},
    ],
}


@pytest.fixture
def client_and_events():
    """TestClient with db.get_problem and db.put_step_event stubbed."""
    events: list[dict[str, Any]] = []

    def fake_get_problem(problem_id: str):
        if problem_id == "missing":
            return None
        return {
            "problem_id": problem_id,
            "user_id": "demo",
            "raw_input": SAMPLE_AI_RESPONSE["normalised_form"],
            "normalised_form": SAMPLE_AI_RESPONSE["normalised_form"],
            "topic_tags": ["differentiation"],
            "difficulty": 3,
            "ai_response": SAMPLE_AI_RESPONSE,
            "created_at": "2026-05-01T00:00:00Z",
        }

    def fake_put_step_event(*, attempt_id, event_type, step_number, payload):
        events.append({
            "attempt_id": attempt_id,
            "event_type": event_type,
            "step_number": step_number,
            "payload": payload,
        })

    with patch.object(db, "get_problem", side_effect=fake_get_problem), \
         patch.object(db, "put_step_event", side_effect=fake_put_step_event):
        yield TestClient(main.app), events


def _evaluate_payload(
    submission: str, problem_id: str = "p1", mode: str = "free",
) -> dict:
    return {
        "attempt_id": "attempt-test",
        "problem_id": problem_id,
        "submission": submission,
        "mode": mode,
    }


# ── Cheap path ──────────────────────────────────────────────────────────────


def test_cheap_path_final_answer_match_skips_llm(client_and_events):
    """When the submission equals the canonical final answer, no LLM call."""
    client, events = client_and_events

    # If the LLM gets called we want the test to fail loudly.
    with patch.object(gcse_evaluator, "_call_llm", side_effect=AssertionError("LLM should not be called")):
        res = client.post(
            "/api/v1/homework/evaluate",
            json=_evaluate_payload("dy/dx = 30x(3x^2 + 2)^4"),
        )

    assert res.status_code == 200
    body = res.json()
    assert body["is_correct"] is True
    assert body["feedback_segments"] == []
    assert body["prose_feedback"] is None

    # And the attempt was logged.
    submitted = [e for e in events if e["event_type"] == "attempt_submitted"]
    assert len(submitted) == 1
    assert submitted[0]["payload"]["is_correct"] is True


def test_cheap_path_handles_normalisation(client_and_events):
    """Whitespace and case differences shouldn't block the cheap-path match."""
    client, _events = client_and_events
    with patch.object(gcse_evaluator, "_call_llm", side_effect=AssertionError("LLM should not be called")):
        res = client.post(
            "/api/v1/homework/evaluate",
            json=_evaluate_payload("DY/DX  =  30X(3X^2 + 2)^4"),
        )
    assert res.json()["is_correct"] is True


# ── LLM path: valid markup ──────────────────────────────────────────────────


def test_llm_path_returns_valid_markup(client_and_events):
    """LLM markup that reconstructs the submission is passed through."""
    client, events = client_and_events
    submission = "y = u^5 with u = 3x^2 + 2"

    fake_llm_response = json.dumps({
        "feedback_segments": [
            {
                "text": "y = u^5",
                "status": "correct",
                "comment": "Good — outer function named.",
            },
            {
                "text": " with u = 3x^2 + 2",
                "status": "correct",
                "comment": None,
            },
        ]
    })

    # Also stub _load_active_prompt so the test doesn't hit DynamoDB.
    with patch.object(gcse_evaluator, "_load_active_prompt", return_value=("sys", "user {{SUBMISSION}}")), \
         patch.object(gcse_evaluator, "_call_llm", return_value=fake_llm_response):
        res = client.post("/api/v1/homework/evaluate", json=_evaluate_payload(submission))

    assert res.status_code == 200
    body = res.json()
    assert body["is_correct"] is False
    assert body["prose_feedback"] is None
    assert len(body["feedback_segments"]) == 2
    # Segments concatenate back to the original submission.
    assert "".join(s["text"] for s in body["feedback_segments"]) == submission
    assert body["feedback_segments"][0]["status"] == "correct"

    # Logged with segment statuses summary.
    submitted = [e for e in events if e["event_type"] == "attempt_submitted"]
    assert submitted[0]["payload"]["segment_statuses"] == ["correct", "correct"]


# ── LLM path: invalid markup → prose fallback ──────────────────────────────


def test_llm_path_invalid_markup_falls_back_to_prose(client_and_events):
    """When segments don't reconstruct the submission, fall back to prose."""
    client, events = client_and_events
    submission = "y = u^5 with u = 3x^2 + 2"

    # Concatenated segments DON'T equal the original — the LLM rewrote it.
    bad_response = json.dumps({
        "feedback_segments": [
            {"text": "y equals u to the fifth", "status": "correct", "comment": "yes"},
        ],
        "prose_feedback": "You correctly identified the outer function.",
    })

    with patch.object(gcse_evaluator, "_load_active_prompt", return_value=("sys", "user {{SUBMISSION}}")), \
         patch.object(gcse_evaluator, "_call_llm", return_value=bad_response):
        res = client.post("/api/v1/homework/evaluate", json=_evaluate_payload(submission))

    assert res.status_code == 200
    body = res.json()
    assert body["is_correct"] is False
    assert body["feedback_segments"] == []
    assert body["prose_feedback"] == "You correctly identified the outer function."

    # Logged with the prose-fallback flag set.
    submitted = [e for e in events if e["event_type"] == "attempt_submitted"]
    assert submitted[0]["payload"]["prose_feedback_used"] is True


def test_llm_path_non_json_falls_back_to_generic_prose(client_and_events):
    """If the LLM returns non-JSON, we fall back to a generic note."""
    client, _events = client_and_events
    with patch.object(gcse_evaluator, "_load_active_prompt", return_value=("sys", "user {{SUBMISSION}}")), \
         patch.object(gcse_evaluator, "_call_llm", return_value="this is not json"):
        res = client.post("/api/v1/homework/evaluate", json=_evaluate_payload("anything"))
    body = res.json()
    assert body["is_correct"] is False
    assert body["feedback_segments"] == []
    assert body["prose_feedback"] is not None  # generic note


def test_llm_path_unknown_status_coerced_to_unclear(client_and_events):
    """A status the LLM invents (e.g. 'partial') is coerced to 'unclear'."""
    client, _events = client_and_events
    submission = "y = u^5"
    weird = json.dumps({
        "feedback_segments": [
            {"text": "y = u^5", "status": "partial", "comment": "kinda right"},
        ]
    })
    with patch.object(gcse_evaluator, "_load_active_prompt", return_value=("sys", "user {{SUBMISSION}}")), \
         patch.object(gcse_evaluator, "_call_llm", return_value=weird):
        res = client.post("/api/v1/homework/evaluate", json=_evaluate_payload(submission))
    body = res.json()
    assert body["feedback_segments"][0]["status"] == "unclear"


# ── Validation errors ──────────────────────────────────────────────────────


def test_empty_submission_400(client_and_events):
    client, _events = client_and_events
    res = client.post("/api/v1/homework/evaluate", json=_evaluate_payload("   "))
    assert res.status_code == 400


def test_missing_problem_404(client_and_events):
    client, _events = client_and_events
    res = client.post(
        "/api/v1/homework/evaluate",
        json=_evaluate_payload("anything", problem_id="missing"),
    )
    assert res.status_code == 404


def test_get_problem_endpoint(client_and_events):
    client, _events = client_and_events
    res = client.get("/api/v1/problems/p1")
    assert res.status_code == 200
    body = res.json()
    assert body["problem_id"] == "p1"
    assert body["ai_response"]["full_solution"].startswith("Let u")


def test_get_problem_missing_404(client_and_events):
    client, _events = client_and_events
    res = client.get("/api/v1/problems/missing")
    assert res.status_code == 404


# ── Markup integrity unit test ─────────────────────────────────────────────


def test_segments_concatenate_to_helper():
    """Direct unit test of the integrity check used inside the evaluator."""
    assert gcse_evaluator._segments_concatenate_to(
        [{"text": "ab"}, {"text": "cd"}], "abcd"
    )
    assert not gcse_evaluator._segments_concatenate_to(
        [{"text": "ab"}, {"text": "cd"}], "abxcd"
    )
    assert not gcse_evaluator._segments_concatenate_to(
        "not a list", "anything"
    )


def test_reconstruct_with_whitespace_inserts_dropped_newline():
    """LLM dropped a \\n between two lines — reconstruct it as a segment."""
    segments = [
        {"text": "y = u^5", "status": "correct", "comment": "Outer named."},
        {"text": "dy/dx = 5u^4", "status": "incomplete", "comment": "Need du/dx."},
    ]
    original = "y = u^5\ndy/dx = 5u^4"
    patched = gcse_evaluator._reconstruct_with_whitespace(segments, original)
    assert patched is not None
    # Concat now equals the original
    assert "".join(s["text"] for s in patched) == original
    # The middle inserted segment is the dropped newline, marked correct
    assert patched[1]["text"] == "\n"
    assert patched[1]["status"] == "correct"
    assert patched[1]["comment"] is None


def test_reconstruct_handles_leading_and_trailing_whitespace():
    """Whitespace before the first segment or after the last is recovered."""
    segments = [{"text": "x = 6", "status": "correct", "comment": None}]
    original = "  x = 6  "
    patched = gcse_evaluator._reconstruct_with_whitespace(segments, original)
    assert patched is not None
    assert "".join(s["text"] for s in patched) == original


def test_reconstruct_rejects_non_whitespace_loss():
    """If anything beyond whitespace was dropped, we don't render markup."""
    segments = [{"text": "x = 6", "status": "correct", "comment": None}]
    original = "let me think... x = 6"  # extra prose dropped
    assert gcse_evaluator._reconstruct_with_whitespace(segments, original) is None


def test_reconstruct_rejects_segment_text_not_in_original():
    """If the LLM wrote text the student didn't, we cannot reconstruct."""
    segments = [{"text": "y = u^6", "status": "wrong", "comment": "wrong exponent"}]
    original = "y = u^5"
    assert gcse_evaluator._reconstruct_with_whitespace(segments, original) is None


def test_llm_path_dropped_newline_recovered_into_segments(client_and_events):
    """End-to-end: LLM drops a newline, reconstruction recovers it, markup is rendered."""
    client, _events = client_and_events
    submission = "y = u^5\ndy/dx = 5u^4"

    # LLM response is missing the \n between the two lines.
    fake_llm_response = json.dumps({
        "feedback_segments": [
            {"text": "y = u^5", "status": "correct", "comment": "Outer named."},
            {"text": "dy/dx = 5u^4", "status": "incomplete", "comment": "Need du/dx."},
        ]
    })

    with patch.object(gcse_evaluator, "_load_active_prompt", return_value=("sys", "user {{SUBMISSION}}")), \
         patch.object(gcse_evaluator, "_call_llm", return_value=fake_llm_response):
        res = client.post("/api/v1/homework/evaluate", json=_evaluate_payload(submission))

    assert res.status_code == 200
    body = res.json()
    # Should NOT have fallen back to prose — reconstruction succeeded.
    assert body["prose_feedback"] is None
    assert body["feedback_segments"], "expected reconstructed segments"
    assert "".join(s["text"] for s in body["feedback_segments"]) == submission


def test_normalise_segments_drops_invalid_entries():
    """A non-dict or missing-text entry invalidates the whole list."""
    assert gcse_evaluator._normalise_segments([
        {"text": "ok", "status": "correct", "comment": "yes"},
        "not a dict",
    ]) == []
    # Missing text field → reject the whole list
    assert gcse_evaluator._normalise_segments([
        {"status": "correct"},
    ]) == []
    # Empty/whitespace comment is normalised to None
    cleaned = gcse_evaluator._normalise_segments([
        {"text": "ok", "status": "correct", "comment": "   "},
    ])
    assert cleaned == [{"text": "ok", "status": "correct", "comment": None}]


# ── Wrong-not-red heuristic ─────────────────────────────────────────────────


@pytest.mark.parametrize("comment,expected_status", [
    # Comments that should trigger promotion to 'wrong'
    ("The derivative of 3x^2 should be 6x, not 3x.", "wrong"),
    ("You used 3x instead of 6x — check the power rule.", "wrong"),
    ("That's incorrect — try differentiating term by term.", "wrong"),
    ("SHOULD BE 6x", "wrong"),  # case-insensitive
])
def test_status_promoted_to_wrong_on_corrective_comment(comment, expected_status):
    cleaned = gcse_evaluator._normalise_segments([
        {"text": "du/dx = 3x", "status": "incomplete", "comment": comment},
    ])
    assert cleaned[0]["status"] == expected_status


@pytest.mark.parametrize("comment", [
    "Good — outer function named.",
    "Right so far, but you'll need to multiply by du/dx.",
    "You haven't shown the next step yet — what comes after this?",
    None,
    "",
])
def test_status_unchanged_on_benign_comment(comment):
    cleaned = gcse_evaluator._normalise_segments([
        {"text": "y = u^5", "status": "correct", "comment": comment},
    ])
    assert cleaned[0]["status"] == "correct"


def test_existing_wrong_status_not_double_processed():
    """If the LLM already labelled it 'wrong', the heuristic shouldn't touch it."""
    cleaned = gcse_evaluator._normalise_segments([
        {"text": "du/dx = 3x", "status": "wrong", "comment": "should be 6x"},
    ])
    assert cleaned[0]["status"] == "wrong"


def test_unclear_status_not_promoted_by_heuristic():
    """Unclear stays unclear even with a corrective-sounding comment."""
    cleaned = gcse_evaluator._normalise_segments([
        {"text": "???", "status": "unclear", "comment": "should be a clearer attempt"},
    ])
    assert cleaned[0]["status"] == "unclear"


# ── Guided mode (next_prompt) ──────────────────────────────────────────────


def test_guided_mode_returns_next_prompt(client_and_events):
    """In guided mode the LLM's next_prompt is surfaced in the response."""
    client, _events = client_and_events
    submission = "y = u^5"
    fake_response = json.dumps({
        "feedback_segments": [
            {"text": "y = u^5", "status": "correct", "comment": "Outer function named."},
        ],
        "next_prompt": "What's du/dx for u = 3x^2 + 2?",
    })
    with patch.object(gcse_evaluator, "_load_active_prompt", return_value=("sys", "user {{SUBMISSION}}")), \
         patch.object(gcse_evaluator, "_call_llm", return_value=fake_response):
        res = client.post(
            "/api/v1/homework/evaluate",
            json=_evaluate_payload(submission, mode="guided"),
        )
    assert res.status_code == 200
    body = res.json()
    assert body["next_prompt"] == "What's du/dx for u = 3x^2 + 2?"


def test_free_mode_drops_next_prompt_even_if_llm_emits_one(client_and_events):
    """The system prompt forbids next_prompt in free mode; defensively drop any."""
    client, _events = client_and_events
    submission = "y = u^5"
    fake_response = json.dumps({
        "feedback_segments": [
            {"text": "y = u^5", "status": "correct", "comment": None},
        ],
        "next_prompt": "Try differentiating.",
    })
    with patch.object(gcse_evaluator, "_load_active_prompt", return_value=("sys", "user {{SUBMISSION}}")), \
         patch.object(gcse_evaluator, "_call_llm", return_value=fake_response):
        res = client.post(
            "/api/v1/homework/evaluate",
            json=_evaluate_payload(submission, mode="free"),
        )
    body = res.json()
    assert body["next_prompt"] is None


def test_invalid_mode_400(client_and_events):
    client, _events = client_and_events
    payload = _evaluate_payload("anything")
    payload["mode"] = "tutor"
    res = client.post("/api/v1/homework/evaluate", json=payload)
    assert res.status_code == 400


def test_render_evaluation_prompt_substitutes_mode():
    from gcse_help_prompts import render_evaluation_prompt
    rendered = render_evaluation_prompt(
        "Mode: {{MODE}}; Sub: {{SUBMISSION}}",
        question="Q",
        canonical_solution="C",
        submission="S",
        mode="guided",
    )
    assert rendered == "Mode: guided; Sub: S"


# ── v3 schema: milestone_answers + simpler_version (Phase 3) ────────────────


def test_final_answer_candidates_prefers_milestone_answers():
    """v3 milestone_answers (top-level) wins over v2 steps[].expected_answer."""
    ai_response = {
        "milestone_answers": ["x = 6"],
        "steps": [{"expected_answer": "x = 5"}],  # v2 fallback — should be ignored
    }
    candidates = gcse_evaluator._final_answer_candidates(ai_response)
    assert candidates == ["x = 6"]


def test_final_answer_candidates_falls_back_to_v2_steps():
    """When milestone_answers is missing (cached pre-v3 problems), use steps[]."""
    ai_response = {
        "steps": [{"expected_answer": "x = 5"}],
    }
    candidates = gcse_evaluator._final_answer_candidates(ai_response)
    assert candidates == ["x = 5"]


def test_build_simpler_payload_extracts_solution_and_question():
    ai_response = {
        "simpler_version": {
            "question": "Solve 2x = 10",
            "solution": "x = 5",
            "opening_prompt": "Single step.",
        }
    }
    payload = gcse_evaluator._build_simpler_payload(ai_response)
    assert payload is not None
    assert payload["full_solution"] == "x = 5"
    assert payload["milestone_answers"] == ["x = 5"]
    assert payload["normalised_form"] == "Solve 2x = 10"
    assert payload["opening_prompt"] == "Single step."


def test_build_simpler_payload_returns_none_when_missing():
    assert gcse_evaluator._build_simpler_payload({}) is None
    assert gcse_evaluator._build_simpler_payload({"simpler_version": {}}) is None
    assert gcse_evaluator._build_simpler_payload({"simpler_version": {"question": "Q"}}) is None


def test_evaluate_target_simpler_uses_simpler_solution(client_and_events):
    """When target=simpler, cheap-path matches against the simpler solution."""
    client, _events = client_and_events

    # Augment the fixture's problem with a simpler_version. We need to
    # override db.get_problem just for this test to inject the v3 field.
    def _get_with_simpler(_pid):
        return {
            "problem_id": "p1",
            "user_id": "demo",
            "raw_input": SAMPLE_AI_RESPONSE["normalised_form"],
            "normalised_form": SAMPLE_AI_RESPONSE["normalised_form"],
            "topic_tags": ["differentiation"],
            "difficulty": 3,
            "ai_response": {
                **SAMPLE_AI_RESPONSE,
                "simpler_version": {
                    "question": "Differentiate y = (x + 1)^2",
                    "solution": "dy/dx = 2(x + 1)",
                    "opening_prompt": "Same shape, smaller numbers.",
                },
            },
            "created_at": "2026-05-02T00:00:00Z",
        }

    with patch.object(db, "get_problem", side_effect=_get_with_simpler), \
         patch.object(gcse_evaluator, "_call_llm", side_effect=AssertionError("LLM should not be called")):
        # Submitting the simpler-version's final answer with target=simpler
        # should cheap-path through to is_correct=True.
        payload = _evaluate_payload("dy/dx = 2(x + 1)", mode="guided")
        payload["target"] = "simpler"
        res = client.post("/api/v1/homework/evaluate", json=payload)

    assert res.status_code == 200
    body = res.json()
    assert body["is_correct"] is True


def test_evaluate_target_simpler_without_simpler_version(client_and_events):
    """If the problem has no simpler_version, target=simpler returns prose, not error."""
    client, _events = client_and_events
    payload = _evaluate_payload("anything", mode="guided")
    payload["target"] = "simpler"
    # Fixture's SAMPLE_AI_RESPONSE has no simpler_version field.
    res = client.post("/api/v1/homework/evaluate", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["is_correct"] is False
    assert body["prose_feedback"] is not None
    assert "simpler version" in body["prose_feedback"].lower()


def test_evaluate_invalid_target_400(client_and_events):
    client, _events = client_and_events
    payload = _evaluate_payload("anything")
    payload["target"] = "elsewhere"
    res = client.post("/api/v1/homework/evaluate", json=payload)
    assert res.status_code == 400


def test_classify_answer_endpoint_removed(client_and_events):
    """Phase 3 deleted the legacy /classify-answer endpoint."""
    client, _events = client_and_events
    res = client.post("/api/v1/homework/classify-answer", json={"anything": True})
    assert res.status_code == 404


# ── v3 ingestion validator (Phase 3) ────────────────────────────────────────


def test_validate_v3_response_accepts_full_shape():
    from gcse_help_generator import GCSEHelpGenerator
    gen = GCSEHelpGenerator.__new__(GCSEHelpGenerator)  # bypass __init__ (no DB)
    obj = {
        "normalised_form": "2x + 5 = 17",
        "topic_tags": ["linear_equations"],
        "difficulty": 2,
        "opening_prompt": "Two-step linear equation.",
        "full_solution": "Subtract 5; divide by 2; x = 6.",
        "milestone_answers": ["2x = 12", "x = 6"],
        "simpler_version": {
            "question": "Solve 2x = 10",
            "solution": "x = 5",
        },
        "explain_it_back": {
            "question": "Why subtract first?",
            "sentence_starters": ["Because…"],
            "rubric": [{"criterion": "x", "description": "y"}],
        },
    }
    # Should not raise.
    gen._validate_v3_response(obj)


@pytest.mark.parametrize("missing_field", ["normalised_form", "full_solution"])
def test_validate_v3_response_rejects_missing_required(missing_field):
    """Only normalised_form and full_solution are strict-required."""
    from gcse_help_generator import GCSEHelpGenerator, GCSEHelpError
    gen = GCSEHelpGenerator.__new__(GCSEHelpGenerator)
    obj = {
        "normalised_form": "...",
        "topic_tags": ["x"],
        "difficulty": 2,
        "opening_prompt": "...",
        "full_solution": "...",
        "milestone_answers": ["..."],
        "simpler_version": {"question": "...", "solution": "..."},
        "explain_it_back": {"question": "...", "sentence_starters": [], "rubric": [{"criterion": "x", "description": "y"}]},
    }
    obj.pop(missing_field)
    with pytest.raises(GCSEHelpError):
        gen._validate_v3_response(obj)


@pytest.mark.parametrize("missing_field", [
    "opening_prompt", "milestone_answers", "simpler_version", "explain_it_back",
])
def test_validate_v3_response_accepts_missing_optional(missing_field):
    """Optional fields can be missing — frontend/evaluator degrade gracefully."""
    from gcse_help_generator import GCSEHelpGenerator
    gen = GCSEHelpGenerator.__new__(GCSEHelpGenerator)
    obj = {
        "normalised_form": "...",
        "topic_tags": ["x"],
        "difficulty": 2,
        "opening_prompt": "...",
        "full_solution": "...",
        "milestone_answers": ["..."],
        "simpler_version": {"question": "...", "solution": "..."},
        "explain_it_back": {"question": "...", "sentence_starters": [], "rubric": [{"criterion": "x", "description": "y"}]},
    }
    obj.pop(missing_field)
    # Should not raise.
    gen._validate_v3_response(obj)


def test_validate_v3_response_rejects_malformed_milestones():
    """If milestone_answers is present, it must be a list of non-empty strings."""
    from gcse_help_generator import GCSEHelpGenerator, GCSEHelpError
    gen = GCSEHelpGenerator.__new__(GCSEHelpGenerator)
    obj_base = {
        "normalised_form": "...", "topic_tags": ["x"], "difficulty": 2,
        "opening_prompt": "...", "full_solution": "...",
        "simpler_version": {"question": "...", "solution": "..."},
        "explain_it_back": {"question": "...", "sentence_starters": [], "rubric": [{"criterion": "x", "description": "y"}]},
    }
    # Wrong type (string not list)
    with pytest.raises(GCSEHelpError, match="milestone_answers"):
        gen._validate_v3_response({**obj_base, "milestone_answers": "x = 6"})
    # List but with empty string
    with pytest.raises(GCSEHelpError, match="milestone_answers"):
        gen._validate_v3_response({**obj_base, "milestone_answers": [""]})


def test_has_valid_simpler_version_helper():
    from gcse_help_generator import _has_valid_simpler_version
    assert _has_valid_simpler_version({"simpler_version": {"question": "Q", "solution": "S"}})
    assert not _has_valid_simpler_version({})
    assert not _has_valid_simpler_version({"simpler_version": "not a dict"})
    assert not _has_valid_simpler_version({"simpler_version": {"question": "", "solution": "S"}})
    assert not _has_valid_simpler_version({"simpler_version": {"question": "Q", "solution": ""}})
    assert not _has_valid_simpler_version({"simpler_version": {"question": "Q"}})  # solution missing


def test_validate_v3_response_rejects_malformed_simpler_version():
    """If simpler_version is present, question and solution are required."""
    from gcse_help_generator import GCSEHelpGenerator, GCSEHelpError
    gen = GCSEHelpGenerator.__new__(GCSEHelpGenerator)
    obj_base = {
        "normalised_form": "...", "topic_tags": ["x"], "difficulty": 2,
        "opening_prompt": "...", "full_solution": "...",
        "milestone_answers": ["..."],
        "explain_it_back": {"question": "...", "sentence_starters": [], "rubric": [{"criterion": "x", "description": "y"}]},
    }
    # simpler_version present but missing solution
    with pytest.raises(GCSEHelpError, match="simpler_version"):
        gen._validate_v3_response({**obj_base, "simpler_version": {"question": "?"}})
    # simpler_version is the wrong type
    with pytest.raises(GCSEHelpError, match="simpler_version"):
        gen._validate_v3_response({**obj_base, "simpler_version": "a string"})
