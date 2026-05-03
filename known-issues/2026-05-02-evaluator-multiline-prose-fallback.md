# Multi-line submissions fall back to prose

**Date observed:** 2026-05-02
**Status:** in-progress (diagnostic logging landed; root-cause fix pending data)
**Severity:** medium
**Area:** evaluator (LLM markup integrity)

## Diagnostic logging in place (2026-05-02)

`gcse_evaluator._log_validation_failure` now logs (at WARNING level) the truncated raw LLM response and the truncated submission whenever markup validation falls back to prose. Search for `evaluate_submission: markup validation failed` in the backend logs to see exactly what the LLM returned for any failing submission.

**Next step in this issue's lifecycle:** trigger the failure once on a real multi-line submission, read the log, identify which character-level normalisation the LLM is doing (almost certainly unicode for `^`/superscripts, or `=` spacing), and pick between the canonical-comparison fix and the difflib reconstruction fix per the options below.


## Symptom

When a student submits working that spans more than one line, the evaluator returns the prose fallback ("I had a look at your working but the feedback didn't come back in a shape I can render reliably…") instead of coloured markup.

A whitespace-tolerant reconstruction step (`gcse_evaluator._reconstruct_with_whitespace`) was added that re-inserts dropped whitespace when the LLM omits it from its segments. That fix handled the simplest failure mode in unit tests, but real submissions still hit the prose fallback — so the LLM is doing something more substantial than just dropping whitespace.

## Reproduction

1. Submit `Differentiate y = (3x^2 + 2)^5 with respect to x` via `/homework`.
2. Click "Try freely instead".
3. Type, with an actual newline between the two lines:

   ```
   y = u^5 with u = 3x^2 + 2
   dy/dx = 5u^4
   ```

4. **Expected:** coloured markup over both lines, line break preserved.
5. **Actual:** prose fallback message, no markup rendered.

Environment:
- `evaluation` prompt active version: 3 (includes a multi-line worked example showing the `\n` should be carried as its own segment).
- Model: `gpt-4.1-mini`.
- Whitespace-reconstruction code is live (verified by passing unit tests in `test_evaluate.py`).

## What we know

- The prompt explicitly tells the model to preserve line breaks and includes a multi-line worked example.
- The reconstruction code handles the case where segments differ from the original *only* by missing whitespace runs. If reconstruction also fails, it means the LLM segments differ in ways beyond whitespace — i.e. the LLM is rewriting characters or normalising in some way that breaks the substring search inside `_reconstruct_with_whitespace`.
- Most likely culprit: the LLM is normalising the student's text inside segments — e.g. swapping ASCII `^` for unicode superscripts (`x^2` → `x²`), normalising spacing around `=`, or replacing the user's `\n` with `\\n` literal. Once the segment text doesn't appear verbatim in the original, `original.find(text, pos)` returns -1 and reconstruction bails.
- Not yet captured: the actual LLM raw response for a failing submission. Adding logging of the raw response on validation failure would let us see exactly what's being returned and pick the right fix.

## Possible fixes

In rough order of cost:

1. **Log the raw LLM response on validation failure.** One-liner in `gcse_evaluator.evaluate_submission`. Without this, every diagnosis of this issue starts with guesswork. Should land *before* trying any other fix so we have data.
2. **Canonicalise both submission and segments before comparing.** Normalise unicode, collapse spacing, lowercase — accept the markup if the canonical forms match, render using the original text wherever a segment can be located in the original substring-wise. Preserves rendering fidelity even when the LLM lightly rewrites.
3. **Use `difflib.SequenceMatcher` for fuzzy reconstruction.** If the LLM segments differ from the original by small character-level edits (not just whitespace), a diff-driven reconstruction can usually patch them. More invasive than (2); only needed if (2) doesn't catch the actual failure mode.
4. **Tighter system prompt with negative examples.** Show the model two failed cases ("here's what NOT to do: rewriting `x^2` as `x²`") alongside the existing positive example. May or may not help; cheap to try.
5. **Model swap.** A stronger model is more likely to preserve verbatim text under instruction. Would also help with the wrong-tagging issue (see other known-issue file). Same env-var approach as suggested there.

(1) is essentially free and unblocks proper diagnosis of (2) vs (3) vs (4). Always do (1) first.

## Workaround

Students can submit one line of working at a time; markup renders fine for single-line submissions. Multi-line is currently unreliable. The frontend doesn't enforce single-line — this is a constraint they discover empirically, which is a poor experience but not blocking validation of the overall engine.
