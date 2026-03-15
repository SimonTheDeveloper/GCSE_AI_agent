# REPOSITORY_MAP.md

## Purpose

This document helps developers and AI coding assistants understand where code should live in this repository.

Use it to:

- navigate the codebase quickly
- find the right extension points
- avoid duplicate implementations
- keep features consistent with the existing architecture

Before implementing a change:

1. inspect the current repository structure
2. find the nearest existing pattern
3. reuse existing components where possible
4. propose the smallest pragmatic change
5. wait for approval before implementing

---

# Recommended Top-Level Structure

This is the intended mental model for the repository. The exact folder names may differ slightly in the real codebase.

```text
repo-root/
├─ frontend/
│  ├─ src/
│  │  ├─ app/
│  │  ├─ components/
│  │  ├─ pages/
│  │  ├─ features/
│  │  ├─ services/
│  │  ├─ hooks/
│  │  ├─ types/
│  │  └─ utils/
│  └─ package.json
│
├─ backend/
│  ├─ app/
│  │  ├─ api/
│  │  ├─ core/
│  │  ├─ models/
│  │  ├─ schemas/
│  │  ├─ services/
│  │  ├─ repositories/
│  │  ├─ prompts/
│  │  ├─ integrations/
│  │  ├─ workers/
│  │  └─ utils/
│  ├─ tests/
│  └─ pyproject.toml
│
├─ infrastructure/
│  ├─ terraform/ or cdk/
│  ├─ docker/
│  └─ deployment/
│
├─ docs/
│  ├─ ARCHITECTURE.md
│  ├─ AI_DEVELOPMENT_GUIDELINES.md
│  └─ REPOSITORY_MAP.md
│
└─ .github/
   ├─ workflows/
   └─ copilot-instructions.md
```

If the existing repository differs from this structure, prefer adapting to the current structure rather than moving many files.

---

# Frontend Map

## Purpose of the frontend

The frontend should stay thin.

Responsibilities:

- collect question input
- display OCR text for correction
- render solved exercises
- request hints
- send follow-up questions
- submit answers
- show student progress
- show parent summary
- handle authentication and billing entry points

The frontend should not contain AI logic.

---

## Suggested frontend areas

### `frontend/src/pages/` or `frontend/src/app/`
Page-level routes.

Typical examples:

- question upload page
- solved exercise page
- dashboard page
- parent summary page
- login/signup page
- billing/settings page

Use this layer for composition, not business logic.

---

### `frontend/src/components/`
Reusable UI components.

Typical examples:

- `QuestionUploadForm`
- `OcrCorrectionEditor`
- `ExerciseView`
- `HintPanel`
- `FollowupBox`
- `AnswerInput`
- `ProgressSummaryCard`
- `TopicWeaknessList`

Keep components small and focused.

---

### `frontend/src/features/`
Feature-specific UI and orchestration.

Typical examples:

- `features/questions/`
- `features/progress/`
- `features/parent/`
- `features/billing/`

This is often the best place for feature-specific state and API integration.

---

### `frontend/src/services/`
HTTP client and API wrappers.

Typical examples:

- `questionApi.ts`
- `exerciseApi.ts`
- `progressApi.ts`
- `billingApi.ts`
- `authApi.ts`

All backend calls should be centralized here or in a nearby feature service.

---

### `frontend/src/types/`
Shared TypeScript types used in the frontend.

Typical examples:

- `Exercise.ts`
- `Attempt.ts`
- `TopicProgress.ts`
- `User.ts`

Types should mirror backend contracts closely.

---

### `frontend/src/utils/`
Small stateless helpers.

Typical examples:

- formatting dates
- display helpers
- local validation helpers

Do not place business workflows here.

---

# Backend Map

## Purpose of the backend

The backend is the system control plane.

Responsibilities:

- validate requests
- orchestrate OCR
- canonicalize questions
- perform cache lookups
- generate Exercise objects
- check answers
- persist data
- track usage
- enforce plan limits
- expose APIs to the frontend

All AI interactions happen here.

---

## Suggested backend areas

### `backend/app/api/`
FastAPI routes and request handlers.

Typical examples:

- `questions.py`
- `exercises.py`
- `progress.py`
- `parent.py`
- `billing.py`
- `auth.py`

Routes should be thin.

They should:
- parse request
- call service layer
- return response

Routes should not contain complex business logic.

---

### `backend/app/core/`
Global application configuration and cross-cutting concerns.

Typical examples:

- settings
- dependency injection helpers
- logging setup
- auth helpers
- environment config

If something is used broadly across the app, it likely belongs here.

---

### `backend/app/models/`
Persistence-oriented models or domain models.

Typical examples:

- `exercise.py`
- `attempt.py`
- `topic_progress.py`
- `usage.py`
- `user.py`

Use this area for durable data structures.

---

### `backend/app/schemas/`
Pydantic request/response schemas and validated DTOs.

Typical examples:

- `exercise_schema.py`
- `question_requests.py`
- `answer_check_schema.py`
- `billing_schema.py`

When an API contract or LLM response needs validation, it should usually live here.

---

### `backend/app/services/`
Core business logic.

This is the most important folder.

Typical examples:

- `ocr_service.py`
- `canonicalization_service.py`
- `exercise_generation_service.py`
- `hint_service.py`
- `followup_service.py`
- `answer_check_service.py`
- `progress_service.py`
- `usage_service.py`
- `billing_service.py`

If logic is central to how the product works, it should normally live in services.

---

### `backend/app/repositories/`
Persistence access wrappers.

Typical examples:

- `exercise_repository.py`
- `attempt_repository.py`
- `topic_progress_repository.py`
- `usage_repository.py`

Repository code should focus on reading/writing data, not policy decisions.

---

### `backend/app/prompts/`
Prompt templates and prompt builders.

Typical examples:

- `exercise_generation_prompt.py`
- `followup_prompt.py`
- `answer_check_prompt.py`

Keep prompts versioned and easy to inspect.

Do not scatter raw prompt strings across unrelated files.

---

### `backend/app/integrations/`
External system integrations.

Typical examples:

- OCR provider client
- LLM provider client
- Stripe client
- S3 client
- Cognito/auth provider client

Wrap third-party APIs so the service layer does not deal with raw SDK details everywhere.

---

### `backend/app/utils/`
Small generic helpers.

Typical examples:

- hashing helper
- date helper
- normalization helper
- retry helper

Business workflows should not be implemented here.

---

### `backend/app/workers/`
Background or asynchronous processing.

Typical future examples:

- curriculum tagging jobs
- content QA jobs
- analytics compaction jobs

Avoid adding workers unless there is a real need.

The MVP should remain mostly synchronous and simple.

---

# Core Domain Objects

## Exercise

The most important object in the system.

Represents a solved question that can be reused.

Likely lives in:

- `backend/app/models/exercise.py`
- `backend/app/schemas/exercise_schema.py`
- `frontend/src/types/Exercise.ts`

Used by:

- generation pipeline
- retrieval endpoint
- hint flow
- follow-up explanations
- answer checking
- analytics

If a new feature touches solved questions, check the Exercise model first.

---

## Attempt

Represents a student interaction with an Exercise.

Likely lives in:

- `backend/app/models/attempt.py`
- `backend/app/repositories/attempt_repository.py`
- `frontend/src/types/Attempt.ts`

Used by:

- progress tracking
- dashboard
- parent summaries
- analytics

---

## TopicProgress

Represents aggregated progress per topic.

Likely lives in:

- `backend/app/models/topic_progress.py`
- `backend/app/services/progress_service.py`
- `frontend/src/types/TopicProgress.ts`

Used by:

- student dashboard
- parent summary
- weak topic surfacing

---

## Usage

Represents monthly product usage and cost-related counters.

Likely lives in:

- `backend/app/models/usage.py`
- `backend/app/services/usage_service.py`
- `backend/app/repositories/usage_repository.py`

Used by:

- plan limits
- billing checks
- cost control

---

# Main User Journeys and Where to Look

## 1. Student uploads a new question

Likely files involved:

- frontend upload page/component
- backend questions route
- OCR service
- canonicalization service
- exercise repository
- generation service

If changing this flow, inspect these areas first.

---

## 2. Student requests the next hint

Likely files involved:

- frontend hint component
- exercises or questions route
- hint service
- attempt/session persistence

Do not introduce a new LLM call unless absolutely required.

---

## 3. Student asks a follow-up question

Likely files involved:

- frontend follow-up UI
- backend follow-up endpoint
- followup service
- prompt builder
- LLM integration wrapper

Keep prompt context small.

---

## 4. Student submits an answer

Likely files involved:

- answer input component
- answer-check endpoint
- answer checking service
- attempt repository
- progress service

Prefer deterministic checks first.

---

## 5. Student views progress dashboard

Likely files involved:

- dashboard page
- progress API client
- progress endpoint
- progress service
- topic progress repository

Dashboard logic should mostly consume prepared backend summaries.

---

## 6. Parent views summary

Likely files involved:

- parent summary page
- parent API client
- parent endpoint
- progress summary service
- auth/access checks

Keep this view simple.

---

# Directory Responsibilities by Concern

## If you are changing API contracts
Look in:

- `backend/app/api/`
- `backend/app/schemas/`
- `frontend/src/services/`
- `frontend/src/types/`

---

## If you are changing persistence
Look in:

- `backend/app/models/`
- `backend/app/repositories/`
- infrastructure definitions if table/index changes are needed

---

## If you are changing prompts or AI behavior
Look in:

- `backend/app/prompts/`
- `backend/app/services/`
- `backend/app/integrations/`
- validation schemas for the returned structure

---

## If you are changing cost-control behavior
Look in:

- `backend/app/services/usage_service.py`
- `backend/app/services/canonicalization_service.py`
- `backend/app/services/exercise_generation_service.py`
- `backend/app/repositories/exercise_repository.py`

---

## If you are changing auth or billing
Look in:

- `backend/app/api/auth.py`
- `backend/app/api/billing.py`
- `backend/app/services/billing_service.py`
- `backend/app/integrations/stripe_client.py`
- `backend/app/core/`

---

# Where New Code Should Usually Go

## Add a new API endpoint
Usually add or update:

- route in `backend/app/api/`
- schema in `backend/app/schemas/`
- service method in `backend/app/services/`
- repository method if persistence changes are needed
- frontend API client wrapper
- frontend page/component updates

---

## Add a new AI-driven workflow
Usually add or update:

- prompt file in `backend/app/prompts/`
- typed response schema in `backend/app/schemas/`
- orchestration in `backend/app/services/`
- integration wrapper only if a provider-level change is needed

Avoid putting prompt logic directly inside route handlers.

---

## Add a new dashboard metric
Usually add or update:

- backend service that computes or aggregates it
- API schema
- frontend type
- dashboard component

Prefer computing metrics in the backend.

---

# Search Strategy for Copilot or Developers

Before writing code, search for:

- existing route with similar shape
- existing repository for similar persistence pattern
- existing service that already owns adjacent logic
- shared schema that could be extended
- shared frontend component that can be reused

Good search examples:

- `exercise_id`
- `hint_1`
- `followup`
- `topic_progress`
- `usage`
- `checkout-session`
- `canonical`
- `hash`

Reuse before creating.

---

# Anti-Patterns to Avoid

Do not:

- add business logic directly in FastAPI routes
- scatter LLM calls across many files
- duplicate prompt templates
- bypass cache lookup for new question generation
- send full chat history for small follow-up explanations
- add heavy abstraction layers for MVP features
- add background jobs for functionality that can be synchronous for now
- create parallel versions of the Exercise schema without approval

---

# Safe Implementation Pattern

For most features, use this order:

1. inspect nearest existing implementation
2. update schema if needed
3. update service logic
4. update repository if needed
5. expose route
6. wire frontend API call
7. update UI
8. add tests

This usually leads to the smallest and safest change set.

---

# Testing Map

## Backend tests
Likely live in:

- `backend/tests/services/`
- `backend/tests/api/`
- `backend/tests/repositories/`

Focus on:

- canonicalization
- cache hit/miss
- exercise generation validation
- answer checking
- progress updates

---

## Frontend tests
Likely live in:

- `frontend/src/**/*.test.tsx`
- `frontend/src/**/*.spec.ts`

Focus on:

- upload flow
- OCR correction UI
- exercise rendering
- hint progression
- dashboard rendering

---

# Documentation Map

Important docs for contributors and AI tools:

- `AI_DEVELOPMENT_GUIDELINES.md` — rules for AI-assisted coding
- `ARCHITECTURE.md` — system design and flow
- `REPOSITORY_MAP.md` — where logic belongs

When implementing features, align with all three.

---

# Final Rule

When unsure where new code belongs:

- prefer extending an existing service rather than creating a new abstraction
- prefer a simple schema change rather than parallel models
- prefer deterministic logic rather than a new AI step
- prefer a small, reviewable PR rather than a broad refactor

The goal is a simple, sellable MVP that remains easy to understand and cheap to run.

