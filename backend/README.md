# Backend

FastAPI backend for the GCSE AI Tutor.

## Structure

```
backend/
├─ main.py                  # FastAPI app and all routes
├─ schemas.py               # Pydantic models (request/response)
├─ database.py / db.py      # DynamoDB helpers (single-table design)
├─ auth.py                  # Cognito JWT verification
├─ gcse_help_generator.py   # AI help orchestration (OpenAI)
├─ gcse_help_prompts.py     # Prompt templates
├─ gcse_help_template.py    # Response templates
└─ scripts/
   └─ compare_maths_problems.py
```

## Running locally

```sh
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn python-dotenv boto3 openai pillow pytesseract
```

Create `.env`:
```env
DYNAMODB_TABLE_NAME=gcse_app
AWS_REGION=eu-west-2
OPENAI_API_KEY=sk-...       # enables AI help on /api/v1/homework/help-json
OPENAI_MODEL=gpt-4o-mini    # optional, defaults to gpt-3.5-turbo
```

Run:
```sh
uvicorn main:app --reload --port 8000
```

## Key endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/v1/diagnostics` | Reports OCR and AI readiness |
| POST | `/api/v1/users/bootstrap` | Create or retrieve user by device ID |
| GET | `/api/v1/subjects` | List subjects and topics |
| GET | `/api/v1/topics/{id}/cards` | Flashcards for a topic |
| POST | `/api/v1/quiz/start` | Start a quiz session |
| POST | `/api/v1/quiz/submit` | Submit answers and get results |
| GET | `/api/v1/review/next` | Cards due for review |
| POST | `/api/v1/homework/submit` | OCR + optional AI help (multipart) |
| POST | `/api/v1/homework/help-json` | Structured AI help (JSON, uses `GCSEHelpGenerator`) |
| POST/GET | `/api/v1/progress` | Save and retrieve student progress |

## Optional integrations

**OCR** — install Tesseract and Python bindings:
```sh
brew install tesseract
pip install pytesseract Pillow
```

**AI help** — set `OPENAI_API_KEY`. The `OPENAI_MODEL` env var selects the model (default `gpt-3.5-turbo`).
