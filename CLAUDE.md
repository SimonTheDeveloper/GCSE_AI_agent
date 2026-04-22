# CLAUDE.md

This file tells Claude Code how to work in this repository.

---

## What this project is

An AI-assisted GCSE tutoring application (initially GCSE Maths).

Students submit questions by image or text. The backend extracts, normalises, and solves the question, building a reusable **Exercise object** that powers hints, step-by-step explanations, answer checking, and progress tracking.

---

## Running the project

### Backend

```sh
cd backend
source .venv/bin/activate          # or: python -m venv .venv && source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

Requires a `.env` in `backend/`:
```
DYNAMODB_TABLE_NAME=gcse_app
AWS_REGION=eu-west-2
OPENAI_API_KEY=sk-...              # enables AI help
```

### Frontend

```sh
cd frontend
npm install
npm run dev                        # starts on http://localhost:5173
```

---

## Actual code structure

### Backend (flat module under `backend/`)

```
backend/
├─ main.py                  # FastAPI app + all route handlers
├─ schemas.py               # Pydantic request/response models
├─ database.py / db.py      # DynamoDB helpers
├─ auth.py                  # Cognito JWT verification
├─ gcse_help_generator.py   # AI help orchestration (OpenAI)
├─ gcse_help_prompts.py     # Prompt templates
└─ gcse_help_template.py    # Response templates
```

The `docs/` files describe an aspirational layered structure (`backend/app/api/`, `backend/app/services/`, etc.) — that is the **target**, not the current state. Add new code to the flat structure; do not reorganise unless explicitly asked.

### Frontend (`frontend/src/`)

```
components/          # Logic containers (state + API calls)
components/views/    # Pure presentational components (stateless, all data via props)
components/ui/       # shadcn/ui primitives — do not modify
```

---

## Key architectural rules

1. **Exercise object is the centre of the system.** Every solved question becomes a reusable Exercise. Do not create parallel schemas without approval.
2. **Cache before generation.** Always canonicalise and look up before calling an LLM.
3. **Hints are stored, not generated live.** Do not add AI calls to hint retrieval.
4. **Backend owns AI.** The frontend must not call model providers directly.
5. **Follow-up prompts stay small.** Send only: cleaned question + relevant solution step + student follow-up. Never send full conversation history.
6. **Validate AI output before storage.** Use Pydantic schemas; never persist unvalidated responses.
7. **Frontend stays thin.** No business logic in components; all AI orchestration in the backend.

---

## Cost-control order

When solving a problem, always prefer in this order:

1. Cached result
2. Deterministic logic
3. Rule-based logic
4. Small AI call
5. Larger AI call (last resort)

Do **not** add AI calls for: hints, dashboards, analytics, usage summaries, progress calculations.

---

## Where to put new code

| What | Where |
|---|---|
| New API endpoint | `backend/main.py` (route) + `backend/schemas.py` (types) |
| New AI workflow | `backend/gcse_help_generator.py` or a new service module + `backend/gcse_help_prompts.py` |
| New DB access | `backend/db.py` |
| New frontend page | `frontend/src/components/` (logic) + `frontend/src/components/views/` (presentational) |
| Shared TS types | `frontend/src/` (co-locate or add a `types/` dir if it grows) |

---

## Implementation approach

Before writing any code:

1. Inspect the relevant files first.
2. Identify what already exists and can be reused.
3. Propose the smallest change that solves the problem.
4. Wait for approval before implementing.

A good change is: small, reviewable, cheap to run, and compatible with the Exercise object model.

---

## Anti-patterns to avoid

- Business logic inside FastAPI route handlers
- LLM calls scattered across multiple files — keep them in `gcse_help_generator.py` or a dedicated service
- Bypassing cache lookup for new question generation
- Duplicating the Exercise schema
- Sending full chat history in follow-up prompts
- Large refactors for small tickets
- Storing unvalidated AI responses

---

## Tests

```sh
# Backend
cd backend && python -m pytest

# Frontend
cd frontend && npm test
```

---

## Further reading

- [docs/AGENT_CONTEXT.md](docs/AGENT_CONTEXT.md) — fuller agent guidance
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system design and data flow
- [docs/EXERCISE_OBJECT_SPEC.md](docs/EXERCISE_OBJECT_SPEC.md) — Exercise object schema
- [docs/repository_map.md](docs/repository_map.md) — target directory structure
- [docs/CONTRIBUTING_AI.md](docs/CONTRIBUTING_AI.md) — AI feature contribution rules
