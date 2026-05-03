# Flexible step progression — leap-ahead detection

**Date:** 2026-05-01
**Status:** decided

## Decision

The number of steps in a stored Exercise stays variable (whatever the LLM produces for that problem), but student *progression* is no longer locked 1:1 to those steps. When a student types into the active step's input box, the backend now matches their answer against every later step's `expected_answer` in addition to the active one. If a forward match is found the student is "leapt" past the intermediate steps:

- The matched step is marked correct (rendered as ✓ Correct).
- The active step plus any intermediates are marked correct *and* skipped, and render as a thin collapsible row with an optional "show working" expansion.
- `activeStep` advances to the step after the matched one.

Wrong-answer classification (format / common-error / arithmetic-slip / conceptual) remains scoped to the active step only. Leap detection is **exact-match only** to avoid false positives where a wrong-answer pattern for step 1 coincidentally equals a downstream step's expected answer.

Skipping is encouraged, not gated: the student does not have to confirm "I did this in my head" or unlock anything. The skipped row is neutral in tone (no celebration, no penalty) and the worked step stays collapsed by default.

Schema additions:

- `ClassifyAnswerReq.remaining_checkpoints: List[Checkpoint]` — every step after the one the student typed into. Optional, defaults to `[]`.
- `ClassifyAnswerRes.matched_step_number: Optional[int]` — set whenever `is_correct` is true. Equal to `req.step_number` on a normal answer; greater on a leap.
- New `step_completed` events emitted on a leap: one per skipped step (`payload.skipped=True, leapt_to=<matched>`) and one for the matched step (`payload.skipped=False, leapt_from=<typed>`).

## Reason

Fixed N steps treated all students as if they need the same decomposition. The problem object's solution path is the right canonical record — it doesn't need to bend per-student — but the *interaction* should. This change:

- Costs nothing extra at runtime: no LLM call, just a string comparison loop over the remaining checkpoints.
- Requires no schema migration of stored Exercises — the existing `expected_answer` per step is already what we need to match against.
- Backwards-compatible: old clients omitting `remaining_checkpoints` still work; the response's new field is optional.
- Sets up cleanly for future "milestones not steps" reframing without committing to it now.

Encouraged-not-gated reflects the user's pedagogical preference: rewarding fluency rather than forcing every student through the textbook decomposition. The collapsed-by-default working keeps the UI calm for the strong student while leaving the option one click away.

## Alternatives considered

**Match in the frontend instead of the backend.** Smaller diff, but normalisation logic would diverge between client (leap detection) and server (current-step classification). Centralising on the server keeps a single source of truth and makes future improvements (e.g. semantic equivalence for algebraically-equal expressions) reach both paths automatically.

**Gate skipping behind a "show your working" toggle.** Rejected per user preference — fluency should be rewarded, not forced into the textbook decomposition.

**Reframe steps as milestones immediately (the change-3 idea).** Ruled out as too large for this ticket. The current change is intentionally additive and reversible; if leap-ahead behaviour proves valuable in usage, the milestone reframe becomes the natural next step. If it doesn't, this can be reverted without touching the data model.

**Apply the full classifier (format / common-error / arithmetic-slip) to checkpoints too.** Would create false leaps where a step-1 wrong-answer pattern accidentally equals a downstream expected answer. Exact-match-only for leap detection is the safer default; the fuzzy logic stays scoped to the step the student is actually working on.
