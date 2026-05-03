# Phase 2 — unified conversational workspace

**Date:** 2026-05-02
**Status:** decided

## Decision

The fixed step-by-step `/homework` UI is removed. Both the previously-deployed step-by-step view (`HomeworkWorkspace`) and the phase-1 free-mode page (`FreeMode`) are replaced by a single unified problem screen at `/homework/:problemId` with three modes that the student can switch between at any time:

- **Guide me** — default. The system shows a tutor-style opening prompt above the first input box. After each submission, the student's working is rendered with markup feedback and a single short *next move* nudge from the system. The conversation stacks vertically, latest at the bottom.
- **Try yourself** — same engine, same markup feedback, but no next-move nudge from the system. The student writes whatever they want; the system stays out of the way.
- **Simpler version** — disabled in the toggle with "coming in Phase 3" tooltip. The shape is established now so it doesn't appear later as a UX surprise.

The opening prompt is **stored on the Exercise object** at problem creation time, not generated on each visit. The v2 ingestion prompt now produces an `opening_prompt` field — one sentence, tutor-style, naming the topic but not the operation. Old cached problems without the field fall back to a generic opener at render time.

The evaluation engine takes a `mode` field on the request. In `guided` mode the LLM is asked to also produce a `next_prompt`. In `free` mode the system prompt forbids next-move suggestions; if one is produced anyway, the evaluator drops it defensively before responding to the client.

A heuristic post-process in the evaluator promotes `correct`/`incomplete` segment statuses to `wrong` when the comment contains corrective phrases ("should be", "instead of", "incorrect"). This works around the model's leniency bias documented in `known-issues/2026-05-02-evaluator-under-tags-wrong.md` rather than trying to talk the model out of it.

The Exercise schema is **not** otherwise migrated in Phase 2. The new flow reads `full_solution` and `steps[].expected_answer` (for cheap-path matching) from the existing v2 shape. The "milestones at top level" reshape, problem-level `common_errors`, and removal of `steps[].nudge|hint|worked_step` are deferred — they touch the generator and cached entries and are better as their own ship.

## Reason

The step-by-step UI plus leap-ahead detection was a partial step toward what the user actually wanted: detailed feedback that engages with what the student wrote and a guidance flow that adapts to where the student is, not a fixed script. Phase 1 proved the markup-feedback engine in free mode. Phase 2 makes that engine the foundation for guided mode too, with the *only* difference between modes being whether the system suggests a next move.

Storing `opening_prompt` on the Exercise (rather than generating it per visit) is the cheap version of "tailored opener": one extra sentence in the existing ingestion call, cached forever after, no per-attempt LLM cost. The user proposed this in design and it slots in cleanly.

Heuristic status repair is independent of the markup pipeline and works with any model. Cheap to add, cheap to remove if a stronger model lands later.

Default mode is *Guide me* because help-seeking students are the larger group; strong students switch in one click. URL is mode-agnostic (`/homework/:problemId`) because mode is a UX preference, not a separate page — the conversation history stays intact across switches.

## Alternatives considered

**Two routes (`/homework/free/:id` and `/homework/guided/:id`) with mode in the URL.** Rejected: shareable URLs are nice but not worth the routing complexity, and switching modes mid-attempt would either reset the conversation or require state to flow through navigation. The single route is simpler and matches the framing.

**Generate the opening prompt per-attempt with a separate LLM call.** Rejected: cost scales with attempts rather than problems, and there's nothing per-attempt for it to specialise on at the start. The "stored on Exercise" version is strictly cheaper and equally good.

**Phase 2 as 2a + 2b (build new flow alongside, then delete old).** Rejected at the user's request: the old UI hadn't been working as intended anyway, the software isn't live, and the parallel-fallback safety net wasn't worth the complexity.

**Migrate the Exercise schema as part of Phase 2.** Rejected: the schema reshape touches the generator prompt, cached entries, and frontend type definitions. Bundling it with the UI rebuild made the ship too big. Better as a separate ticket once Phase 2 + 3 are stable.

**Fix the wrong-not-red issue in the prompt rather than with a heuristic.** Rejected: prompt v3 already has an explicit worked example for this exact case and the model still mislabels. The heuristic is small, deterministic, easy to remove if a stronger model fixes the problem at source. Documented in the known-issue file with a path forward.
