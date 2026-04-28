# Homework UX — codebase analysis and design decisions

This document records the gap analysis between the homework-ux-tickets and the current codebase state, plus design decisions made during the planning session. Use this as context when starting implementation.

---

## Current codebase state (as of 2026-04-27)

### What already exists

**Backend AI generation (gcse_help_generator.py)**
- Runs one AI call at ingestion time and caches the result in DynamoDB — correct architecture
- Returns 5 tiers: `nudge`, `hint`, `steps`, `worked`, `teachback` — top-level, not per-step
- Uses `gpt-4.1-mini` by default (configurable via `OPENAI_MODEL` env var)
- Cache key includes `schema_version` + `prompt_version` (added during this session)

**Prompt management system (built during this session)**
- All four prompts are stored in DynamoDB and editable via `/admin/prompts`
- Admin UI is at `http://localhost:5173/admin/prompts`, gated by `X-Admin-Key` header (set `ADMIN_API_KEY` in `.env`)
- Ingestion prompt v1 = old schema (currently active), v2 = new design from `prompt-design.md` (draft)
- `similar`, `score`, `classify` prompts are seeded and ready to use when their endpoints are built
- Backend endpoints: `GET/PUT /api/v1/admin/prompts/{id}`, `POST /api/v1/admin/prompts/{id}/try`

**Frontend help UI**
- `ExplanationPanel.tsx` — renders steps with status indicators (completed/current/pending)
- `MathProblem.tsx` — binary correct/incorrect checking, shows hint button after wrong answer
- No locked-card rung UI exists yet
- The worked solution is currently visible alongside the input — **this is the leak Ticket 1.1 fixes**

**Data model**
- DynamoDB single-table; has `Cache`, `Progress`, `QuizResult` records
- No `problems`, `attempts`, or `step_events` equivalents — all of Ticket 1.4 is new work

---

## Gap analysis by ticket

### Ticket 1.1 (rung UI)
- Backend data is roughly in the right shape (5 tiers → 4 rungs maps cleanly)
- **All work is frontend.** Replace ExplanationPanel with locked-card layout
- Critical: content must be withheld from the DOM, not just hidden with CSS (copy-paste leak)
- The 5-tier → 4-rung mapping: `nudge` → Rung 1, `hint` → Rung 2, `steps` → Rung 3, `worked` → Rung 4. `teachback` becomes the Ticket 2.1 explain-it-back material.

### Ticket 1.2 (structured AI response)
- Backend already generates at ingestion time and caches — the architecture is right
- The schema needs restructuring: tiers are currently top-level, not per-step
- `common_errors` per step doesn't exist at all
- New ingestion prompt (v2) is already drafted in DynamoDB — activate it once the frontend can parse the new schema
- Bump `schema_version` when activating; the cache key includes it so old cached responses don't break silently
- **Model note:** the ingestion prompt is significantly more complex than the current one. Consider upgrading from `gpt-4.1-mini` for ingestion while keeping cheaper model for follow-ups.

### Ticket 1.3 (wrong-answer diagnostic)
- Almost entirely new work
- Classification should run on the backend, not frontend (keeps frontend thin per CLAUDE.md rules)
- Frontend sends `{raw_input, expected_answer, step_number}`; backend returns `{error_category, redirect_question}`
- Classification order: (1) format check, (2) match against `common_errors` patterns, (3) arithmetic-slip heuristic, (4) call the `classify` prompt in DynamoDB
- The `classify` prompt is already seeded and ready to use as the fallback (step 4)

### Ticket 1.4 (data model)
- Highest-effort ticket; sketch DynamoDB access patterns before writing any code
- Key access patterns needed:
  - All attempts for user X in last 7 days
  - All step_events for attempt Y
  - Most recent attempt for problem Z by user X
- These require careful PK/SK choices and likely a new GSI

### Ticket 2.1 (explain-it-back)
- The `teachback` tier in the current AI response is related but is static content, not interactive
- The `explain_it_back` field in the new ingestion schema (v2) produces the question + starters + rubric at ingestion time
- The `score` prompt in DynamoDB is ready to use for scoring submitted explanations

### Tickets 2.2, 3.x
- All new work; no foundation exists yet
- Don't build Milestone 3 until there are several hundred real attempts in the database

---

## Design decisions made

**Step-by-step rung advancement**
Students advance through steps sequentially. Only the current step's 4-rung ladder is shown. Completed steps collapse to a summary row (step number + student's answer). Future steps are not rendered until unlocked by a correct answer. The rung reveal state is per-step, not global.

**Error classification lives in the backend**
Frontend sends raw input; backend classifies. Keeps AI orchestration out of the frontend per CLAUDE.md architectural rules.

**System and user prompts stored separately**
Each prompt record in DynamoDB has two fields: `systemPrompt` and `userPromptTemplate`. The user template uses `{{BASE_STRUCTURE}}` as a placeholder (replaced at runtime with the problem JSON for the ingestion prompt; descriptive placeholders for the others until their endpoints are built).

**Prompt versioning**
- `schema_version` in the cache key tracks the output shape
- `prompt_version` in the cache key tracks which prompt text produced a given cached response
- Editing a prompt via the admin UI automatically busts the exercise cache for all problems (correct behaviour — they'll be regenerated with the new prompt on next request)
- Always keep old prompt versions; never delete them. You need them to reproduce scoring decisions if a student disputes a result.

**Ingestion model upgrade**
The ingestion prompt v2 is more complex than v1. Test on hard examples before deciding to stay on `gpt-4.1-mini` or upgrade. The three follow-up prompts (similar, score, classify) can stay on a cheaper/faster model.

---

## Files changed during this session

| File | What changed |
|---|---|
| `backend/db.py` | Added prompt CRUD functions (`get_prompt_active`, `get_prompt_version`, `list_prompt_versions`, `put_prompt_version`, `list_prompts`) |
| `backend/gcse_help_prompts.py` | Converted to module constants with `seed_ingestion_prompt_if_missing()`; added `render_user_prompt()` |
| `backend/gcse_help_generator.py` | Loads active prompt from DynamoDB at startup; in-memory prompt cache; `prompt_version` included in cache key hash; `reload_prompt()` method |
| `backend/schemas.py` | Added admin prompt schemas (`PromptSummary`, `PromptVersion`, `PromptSaveReq`, `PromptSaveRes`, `PromptTryReq`, `PromptTryRes`) |
| `backend/main.py` | Five admin endpoints + startup seed event |
| `backend/seed_prompts.py` | One-off script to seed all four prompts from the design documents |
| `frontend/src/lib/api.ts` | Added admin API functions |
| `frontend/src/components/AdminPrompts.tsx` | New component: key-entry → list (with prompt content inline) → editor + version history + test panel |
| `frontend/src/App.tsx` | Added `/admin/prompts` route (bypasses login, uses its own key-based auth) |

---

## Prompt documents

The full prompt designs are in:
- `docs/prompt-design.md` — problem-ingestion prompt (new schema) + three follow-up prompts
