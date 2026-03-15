# REPO_BRAIN.md

## Purpose

This file is a compact high-signal briefing for AI coding agents and human contributors.

Use it to reduce navigation mistakes, duplicated code, and architecture drift.

Read this before implementing any feature.

---

# Repository identity

This is the **GCSE tutoring product repository**.

It contains the app that students and parents use.

It is expected to contain:

- frontend UI
- backend API
- persistence models
- AI prompt and orchestration code
- progress tracking
- billing/auth integration

It is **not** the separate repository that contains the LangGraph coding agent.

---

# Product in one paragraph

A student submits a GCSE maths question by image or text.
The backend extracts and normalizes the question, checks whether an equivalent solved question already exists, and either reuses that Exercise or generates a new one.
The resulting Exercise powers hints, explanations, answer checking, and progress tracking.

---

# The 5 most important truths

## 1. Exercise is the centre of the system
Every solved question should become a reusable Exercise object.

## 2. Cache before generation
Never generate first and deduplicate later.
Canonicalize and look up first.

## 3. Hints are stored, not generated live
Hint requests should usually return pre-generated stored hints.

## 4. Follow-up prompts must stay small
Use the cleaned question, the relevant solution step, and the student’s follow-up.
Do not send the whole conversation.

## 5. Backend owns AI
The frontend should not call model providers directly.

---

# Likely code ownership

## Backend
Owns:
- OCR orchestration
- canonicalization
- cache lookup
- Exercise generation
- answer checking
- progress aggregation
- usage tracking
- billing enforcement

## Frontend
Owns:
- upload UI
- OCR correction UI
- Exercise display
- hint request UI
- follow-up input UI
- dashboard rendering

---

# Strong implementation defaults

When adding or changing code:

- extend existing schemas if appropriate
- extend existing services if appropriate
- update repositories only when persistence changes
- keep route handlers thin
- validate AI output before persistence
- add small targeted tests

---

# Search order for new tasks

When you receive a task, inspect in this order:

1. relevant route or page
2. related service
3. related schema
4. related repository
5. related prompt file
6. related test file

This usually reveals the correct extension point.

---

# Safe planning checklist

Before implementation, write down:

- existing files likely involved
- reusable components
- exact files to modify
- any new files truly needed
- tests to run
- architecture rules that must not be broken

---

# High-risk mistakes

These are especially harmful in this repo:

- duplicating the Exercise schema
- adding LLM calls in hint logic
- bypassing cache lookup
- pushing business logic into route handlers
- creating parallel service layers
- introducing large refactors for small tickets
- storing unvalidated AI responses

---

# Low-risk ticket types

Good candidates for incremental implementation:

- add endpoint
- extend service logic
- add repository method
- add tests
- add progress summary field
- add usage counter
- add dashboard card

---

# High-risk ticket types

Handle with extra care:

- auth redesign
- billing redesign
- infrastructure migration
- major schema changes
- large frontend rework
- introducing live multi-agent orchestration

---

# Minimal change philosophy

The right change is usually the smallest one that:

- solves the issue
- keeps architecture intact
- preserves existing conventions
- keeps costs predictable
- remains easy to review

If tempted to refactor broadly, stop and justify it first.

---

# Files that usually matter most

If present, these should heavily influence implementation:

- `.github/copilot-instructions.md`
- `docs/ARCHITECTURE.md`
- `docs/EXERCISE_OBJECT_SPEC.md`
- `docs/REPOSITORY_MAP.md`
- `docs/CONTRIBUTING_AI.md`
- `docs/AGENT_CONTEXT.md`

These define the intended way of working in the repo.

---

# Final rule

Inspect first.
Plan second.
Implement third.
Validate fourth.

Never skip directly from issue text to code changes.
