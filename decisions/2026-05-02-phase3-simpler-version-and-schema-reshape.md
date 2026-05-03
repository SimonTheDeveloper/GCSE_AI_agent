# Phase 3 — simpler-version mode and Exercise schema reshape

**Date:** 2026-05-02
**Status:** decided

## Decision

Three things shipped together:

**1. The third UX mode lands.** *Try a simpler version first* on the toggle becomes active when the Exercise carries a `simpler_version` payload. The student sees the simpler problem, the simpler opening prompt, and submits working that's evaluated against the simpler solution by the same engine that powers main-track guided mode. On cheap-path success, a one-click *Try the original* button switches them back to guided mode on the main problem. While in simpler mode, main-track conversation history is hidden; switching back restores it. The simpler-mode submissions are kept and reappear on the next visit to simpler mode.

**2. Exercise schema reshapes from v2 to v3.** A new ingestion prompt produces:

```
normalised_form, topic_tags, difficulty
opening_prompt
full_solution
milestone_answers: [str]      # promoted from steps[].expected_answer
simpler_version: { question, solution, opening_prompt? }
explain_it_back
_schema_version: "3.0.0"
```

Everything per-step (`steps[].nudge`, `.hint`, `.worked_step`, `.common_errors`) is gone. With it, the ingestion call gets noticeably smaller — the v2 prompt was paying tokens for content nothing reads under the Phase-2 architecture.

**3. The legacy `/api/v1/homework/classify-answer` endpoint and its surrounding schemas are deleted.** `ClassifyAnswerReq`, `ClassifyAnswerRes`, `Checkpoint`, `CommonErrorIn`, `_normalise_answer`, `_has_numeric_content`, `_extract_rhs_number`, `_log_wrong_answer`, and `test_classify_answer.py` all go away. They served the step-by-step UI that Phase 2 deleted; nothing has called them since.

The evaluator gains a `target` field (`"main"` | `"simpler"`, default `"main"`). When `target="simpler"`, it synthesises a v3-shaped sub-payload from `simpler_version` and runs the same cheap-first → LLM-markup → reconstruction → prose-fallback pipeline against it. The rest of the evaluator doesn't need to know it's a simpler version.

The cheap-path canonical-answer reader prefers the v3 shape (`milestone_answers[-1]`) and falls back to the v2 shape (`steps[-1].expected_answer`) so cached pre-v3 problems keep working through the cache turnover. The v2 fallback can be removed once cache attrition completes.

A diagnostic-logging step also lands here (the first item from the multi-line known-issue): when markup validation falls through to the prose fallback, the raw LLM response and submission are logged at WARNING level to support root-causing the multi-line failure mode.

## Reason

**Why ship the schema reshape now.** After Phase 2, a third of every ingestion-call's output was dead bytes — nothing read `steps[].nudge|hint|worked_step|common_errors` anymore, and the AI quality issues you saw in the integral example confirmed there was no point keeping them as a dormant safety net. The simpler-version work was already touching the ingestion prompt and validator, so doing the reshape in the same change ships one cache turnover instead of two.

**Why a v2 fallback in the evaluator instead of forcing cache regeneration.** Schema bumps invalidate the cache via the cache key already, so cached entries naturally regenerate on next access. The fallback is for in-flight transitions and any cached entry being read between schema bump and regeneration — a small but cheap belt-and-braces.

**Why simpler-mode is always scaffolded.** The student picked simpler-version because they wanted gentler practice; making them choose between guided and free *within* the simpler track is a decision they shouldn't have to make. Mode mapping is `simpler → (mode=guided, target=simpler)`.

**Why hide main history when in simpler mode (and vice versa).** Single focus. The student's working on one problem at a time even though there are technically two tracks. Conversation timeline interleaving the two tracks would be visually noisy.

**Why a one-click "try the original" suggestion on simpler success.** Closing the loop. The whole point of the simpler version is to build confidence to attempt the original; without the prompt, students who solve the simpler one would just sit on the success screen.

**Why the diagnostic logging now.** Was the cheapest item in the multi-line known-issue file's "possible fixes" list, and the prerequisite for any actual fix. Without seeing the raw LLM output on a failing submission, every other proposal is guesswork.

## Alternatives considered

**Keep `steps[]` around as defensive data.** Rejected — nothing reads it and the AI quality on its content was demonstrably mediocre. Carrying dead data costs ingestion tokens forever and gives the impression there's still a step-by-step path lurking.

**Generate the simpler version per-attempt.** Rejected — the simpler version doesn't depend on the student, only on the original problem. Cache-once, use-many fits.

**Ship `simpler_version` only and defer the wider reshape.** Rejected as over-cautious. The reshape risk is bounded by the v2 fallback in the evaluator; we'd still be paying ingestion tokens for dead fields if we kept them.

**Make the simpler-version mode `mode=free, target=simpler` configurable.** Rejected — adds UI complexity (a mode-within-a-mode), and the use case (a strong student wanting to try the simpler version *unscaffolded*) is rare enough that solving it later is fine if it ever surfaces.

**Carry main-track history visibly while in simpler mode.** Rejected per the user's UX call — single focus is the right default. Easy to revisit if students request it.

**Migrate cached v2 entries into v3 shape via a one-off backfill script.** Rejected — natural cache turnover handles it, and the v2 fallback in the evaluator covers the gap. Backfill scripts are debt-y; not worth it for a personal-scale codebase.
