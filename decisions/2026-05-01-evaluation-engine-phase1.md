# Evaluation engine, phase 1 — markup feedback in free mode

**Date:** 2026-05-01
**Status:** decided

## Decision

The fixed step-by-step guided experience is being replaced. The new model has three modes available at any time on a problem:

- **Try your own way** (free mode) — the student types whatever working they want, partial or complete, and submits it for evaluation.
- **Guide me through it** — same evaluation engine, but the system also generates a next prompt in response to what the student just did. Steps are *not* pre-numbered or pre-decomposed; the path emerges from the dialogue.
- **Try a simpler version first** — a slim warm-up record stored on the Exercise (just question + solution + optional nudge).

Across all three modes, evaluation is shared:

1. Cheap match: exact normalised match against the canonical final answer or any milestone answer. Returns immediately, no LLM call.
2. LLM evaluation: send the question, the canonical solution, and the student's submission to an LLM. The LLM returns the submission re-segmented, each segment tagged with a status (`correct` / `incomplete` / `wrong` / `unclear`) and an optional comment. The frontend renders each segment with appropriate styling — markup feedback rather than prose.
3. Markup integrity check: joining `segment.text` in order must equal the original submission character-for-character. On mismatch we return a plain-prose fallback rather than render misaligned markup.

The Exercise object will eventually shrink — `steps[]` goes away, `milestone_answers` and problem-level `common_errors` and `simpler_version` come in. That migration lands with phase 2/3, not phase 1.

This phase ships only what is needed to validate the markup pipeline:

- A new endpoint `/api/v1/homework/evaluate` doing cheap-first → LLM → markup-validate → fallback.
- A new admin-managed prompt (`evaluation`) seeded into the existing prompt-management table so the markup-quality prompt can be tuned without redeploys.
- A new GET `/api/v1/problems/{id}` endpoint to fetch a stored problem (needed by the new route).
- A new frontend route at `/homework/free/{problemId}` rendering a minimal free-mode UI: question, multi-line input, Check button, markup feedback rendered below.
- A "Try freely" link from the existing `HomeworkWorkspace` that navigates to the new route.

Phase 1 deliberately does **not** include:

- A mode-switcher UI. Lands with phase 2 once guided mode is also rebuilt on the same engine.
- Migration of the Exercise schema. Phase 1 reads `full_solution` and `steps[].expected_answer` from the existing v2 shape — no schema change.
- Caching of LLM evaluations. Important but a topic of its own; revisit later.
- Replacement of the existing step-by-step UI. The old route stays parallel until phase 2 supersedes it.

## Reason

The shipped step-by-step guided mode + leap-ahead detection didn't reach the underlying frustration: students submit short answers, get a binary right/wrong, and never see the system engage with what they actually wrote. Detailed feedback requires the system to *read* the working — that's an LLM job, and there's no cheap way around it for the fallback path. Cheap-first matching keeps simple cases free; the LLM only handles novel partial work.

Markup over prose because pedagogically it's much more powerful — the student sees their own working with the right parts ticked and the problematic line specifically named, rather than an essay about it. The cost is reliability: the LLM has to reproduce the student's text faithfully. Validating the segments against the original is the safeguard.

Phasing free mode first because it's the cleanest place to validate the markup pipeline (no `next_prompt` complexity), and the engine that drives free mode also drives guided mode in phase 2.

Storing the evaluation prompt through admin from day one because markup quality is going to need real iteration on real student submissions, and that iteration shouldn't require a deploy each time.

## Alternatives considered

**Keep the step-by-step UI and bolt on prose feedback.** Cheaper in the short term; rejected because the underlying step-by-step model is what the user found restrictive. Adding feedback on top would still leave the gating, the predetermined decomposition, and the answer-as-one-line UX.

**Plain prose feedback instead of markup.** Much easier to build. Rejected because the user identified the lack of *engagement with what the student wrote* as the deepest frustration. Prose can comment on the working but can't tick the right parts and red-flag the wrong line. Markup is the pedagogically correct shape; the build cost is justified.

**LLM-generate the simpler version on demand vs. pre-generate and store.** Pre-generate stored (slim form) wins per the project's cost-control rules in `CLAUDE.md`. One generator-pass at problem creation, free thereafter.

**Build all three modes in one push.** Bigger ship, more risk of something feeling off before you can react. Phasing lets the engine be validated on free mode (minimal UI) before it's wrapped in guided-mode complexity.

**Hardcode the evaluation prompt for phase 1.** Simpler integration. Rejected because tuning the markup-quality prompt is going to be the main iteration loop in the early days of this engine, and going through the admin system from day one means that iteration doesn't block on deploys.
