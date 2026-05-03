# Evaluator under-tags `wrong`

**Date observed:** 2026-05-02
**Status:** in-progress (heuristic mitigation landed; underlying model behaviour unchanged)
**Severity:** medium
**Area:** evaluator (LLM prompt / model behaviour)

## Mitigation in place (2026-05-02)

A heuristic post-process now runs inside `gcse_evaluator._normalise_segments`: when a segment is tagged `correct` or `incomplete` *and* its comment contains one of `"should be"`, `"instead of"`, or `"incorrect"` (case-insensitive), the status is promoted to `wrong`. Logged at INFO level when it fires.

This catches the specific failure mode reported in validation (the `du/dx = 3x` case) and doesn't fight the model — it works around the leniency bias rather than trying to reason it out. Tests are in `test_evaluate.py`.

**What this does NOT solve:** if the model produces a corrective comment without one of those three phrases ("not 6x", "you've used the wrong derivative", "miscalculated"), the heuristic doesn't fire and the segment stays mislabelled. Watch for these in production data and extend the phrase list — or escalate to a model swap as below.


## Symptom

When a student submits mathematically incorrect working, the LLM correctly identifies the mistake in the comment but tags the segment with status `correct` or `incomplete` instead of `wrong`. The frontend then renders the segment in green or amber where it should be red.

The comment content is right; only the status label is wrong. So the student gets accurate written feedback but a misleading colour cue.

## Reproduction

1. Submit `Differentiate y = (3x^2 + 2)^5 with respect to x` via `/homework`.
2. Click "Try freely instead" on the workspace screen.
3. Type `du/dx = 3x` and click Check.
4. **Expected:** the segment is highlighted red, with a comment naming the mistake (e.g. "the derivative of 3x² is 6x, not 3x").
5. **Actual:** the comment is correct but the segment is highlighted green or amber (i.e. tagged `correct` or `incomplete`).

Environment:
- `evaluation` prompt active version: 3 (includes an explicit worked example using exactly this `du/dx = 3x` input, demonstrating that the correct status is `wrong`).
- Model: `gpt-4.1-mini` (default `OPENAI_MODEL`).
- Temperature: 0.2.

## What we know

- The prompt has been strengthened twice — first to add explicit "DO NOT use 'incomplete' for incorrect maths" instruction, then again with a worked example using this very input. The model still mislabels.
- The model's *natural-language reasoning* in the comment is correct ("the derivative of 3x² is 6x, not 3x"), so it has identified the error. The failure is purely in the structured-status field.
- Hypothesis: `gpt-4.1-mini` is biased toward leniency / encouragement when grading, and that bias overrides the explicit instruction. Larger models likely do better.
- Not tested: whether a stronger model (`gpt-4o`, `gpt-4.1`) follows the instruction more reliably.

## Possible fixes

Cheap-to-try first:

1. **Heuristic post-processing in the evaluator.** After parsing segments, scan each comment for negation phrases ("not", "should be", "instead of", "isn't", "incorrect"). If the comment names a mistake but the status is `correct` or `incomplete`, force-promote to `wrong`. Fast, cheap, doesn't fight the model — works around the bias rather than trying to reason it out of existence.
2. **Lower temperature to 0.0** for the evaluation call. Currently 0.2. Low-stakes change; might tighten the model's adherence to the explicit definitions.
3. **Few-shot expansion of the prompt** with 4–5 wrong/incomplete examples covering different mistake types (arithmetic slip, wrong operation, wrong simplification, missing factor). The current prompt has one wrong example; more might tilt the model.
4. **Model swap for evaluation specifically.** Add a separate `OPENAI_MODEL_EVAL` env var defaulting to `gpt-4o`, leave generation on `gpt-4.1-mini`. Has cost implications.
5. **Two-pass evaluation.** First call labels segments. Second call ("Are these labels consistent with the comments?") verifies/corrects. Doubles latency and cost; only worth it if (1)–(4) all fail.

The cheapest meaningful fix is probably (1) — a tightly-scoped heuristic in `gcse_evaluator._normalise_segments` (or a new `_repair_status_against_comment` step). Failing that, escalate.

## Workaround

None currently. The student gets the right written feedback but a misleading colour. Acceptable for an internal preview; not acceptable for actual learners.
