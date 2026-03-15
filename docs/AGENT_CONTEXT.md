# AGENT_CONTEXT.md

## Purpose

This file gives an AI coding agent the minimum context needed to work safely and effectively in this repository.

Read this file before planning or implementing any change.

This repository is the **product repository** for the GCSE tutoring system.
It is not the tooling repository for the LangGraph issue agent.

---

# What this repository is

This repository contains an **AI-assisted GCSE tutoring application**, initially focused on **GCSE Maths**.

Main user journey:

1. student uploads or types a question
2. OCR extracts or cleans the text
3. the system canonicalizes the question
4. the system checks for an existing Exercise object
5. if found, the cached Exercise is reused
6. if not found, a new Exercise is generated and stored
7. the student can request hints, ask follow-up questions, and submit answers
8. progress is tracked for student and parent views

---

# What matters most

The most important concept in this repository is the **Exercise object**.

Every solved question should become a reusable structured asset.

The Exercise object is reused for:

- hints
- follow-up explanations
- answer checking
- analytics
- progress tracking
- curriculum tagging

Do not create parallel versions of the Exercise schema without explicit approval.

---

# Core engineering rules

When making changes:

1. inspect the repository first
2. identify what already exists
3. reuse existing services, routes, schemas, and repositories where possible
4. propose the smallest pragmatic implementation
5. wait for approval before implementing
6. keep the final change set as small as possible

Avoid large refactors unless explicitly requested.

---

# Cost-control rules

AI calls are expensive and should be minimized.

Always prefer this order:

1. cache lookup
2. deterministic logic
3. rule-based logic
4. small AI call
5. stronger AI call only if truly necessary

Do not introduce unnecessary AI calls.

Especially avoid adding AI calls for:

- hint retrieval
- dashboards
- progress summaries
- usage summaries
- simple analytics

---

# Important architecture rules

- The frontend should stay thin.
- The backend owns AI orchestration.
- The backend should validate AI outputs before storing them.
- Prompts should be short and structured.
- Follow-up explanations should not include full chat history.
- New question generation should not bypass canonicalization and cache lookup.

---

# Files you should read first

Before planning a change, read these files if they exist:

1. `.github/copilot-instructions.md`
2. `docs/ARCHITECTURE.md`
3. `docs/EXERCISE_OBJECT_SPEC.md`
4. `docs/REPOSITORY_MAP.md`
5. `docs/CONTRIBUTING_AI.md`

These files define the architecture, coding rules, and object model.

---

# Typical ownership model

Use this mental model when placing code:

- API routes: request parsing and response only
- services: business logic
- repositories: persistence
- schemas: request/response and validated structures
- prompts: AI prompt templates
- frontend services: API calls
- frontend components: UI only

Prefer extending an existing service over introducing a new abstraction.

---

# Anti-patterns to avoid

Do not:

- add business logic directly in API routes
- scatter LLM calls across many files
- duplicate prompts in multiple places
- bypass cache lookup
- regenerate hints with an AI call
- send full conversation history for small follow-up questions
- introduce heavy abstractions for MVP features
- redesign the architecture when a local extension is enough

---

# What a good implementation plan looks like

A good plan should answer:

1. what already exists?
2. what is the smallest change that solves the issue?
3. which files should change?
4. what should not change?
5. which tests should be added or run?

If you cannot answer these questions yet, inspect more before proposing implementation.

---

# Success criteria for this repository

A good change is:

- small
- understandable
- reviewable
- easy to debug
- compatible with the Exercise object model
- cheap to run
- aligned with the current architecture

The goal is not perfect architecture.
The goal is a practical, sellable, maintainable MVP.
