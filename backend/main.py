import logging
import os
import random
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4
from dotenv import load_dotenv
import db
import shutil
import schemas
from auth import get_default_verifier
from auth import get_current_principal

from db import (
    get_user_profile, put_user_profile, get_uid_by_device,
    list_topics_grouped, list_cards_for_topic,
    save_quiz_session, get_quiz_session, delete_quiz_session,
    save_quiz_result, recent_wrong_cards,
)

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form, Depends, status
from fastapi.middleware.cors import CORSMiddleware

from schemas import (BootstrapReq, BootstrapRes, BreakdownItem, Card,
                        NextSteps, Question, QuizStartReq, QuizStartRes, QuizSubmitReq,
                        QuizSubmitRes, ReviewDueGroup, ReviewNextRes,
                        SubjectWithTopics, TopicCardsRes, TopicStub,
                        HomeworkSubmitRes, HomeworkHelpJsonReq, HomeworkHelpJsonRes,
                        PromptSummary, PromptVersion, PromptSaveReq, PromptSaveRes,
                        PromptTryReq, PromptTryRes,
                        AttemptSummary, UserAttemptsRes,
                        LogEventReq, LogEventRes,
                        EvaluateReq, EvaluateRes, FeedbackSegment, ProblemRes)



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "gcse_app")
GSI1_NAME = os.getenv("DYNAMODB_GSI1", "GSI1")

app = FastAPI()


@app.on_event("startup")
def _seed_prompts_on_startup():
    try:
        from gcse_help_prompts import (
            seed_ingestion_prompt_if_missing,
            seed_v2_ingestion_prompt_if_missing,
            seed_v3_ingestion_prompt_if_missing,
            seed_evaluation_prompt_if_missing,
        )
        seeded_v1 = seed_ingestion_prompt_if_missing()
        seeded_v2 = seed_v2_ingestion_prompt_if_missing()
        seeded_v3 = seed_v3_ingestion_prompt_if_missing()
        seeded_eval = seed_evaluation_prompt_if_missing()
        if seeded_v1:
            logger.info("startup: ingestion prompt v1 seeded into DynamoDB")
        if seeded_v2:
            logger.info("startup: ingestion prompt v2 seeded as draft — activate via /admin/prompts when ready")
        if seeded_v3:
            logger.info("startup: ingestion prompt v3 seeded as draft — activate via /admin/prompts when ready")
        if seeded_eval:
            logger.info("startup: evaluation prompt seeded into DynamoDB")
        if not (seeded_v1 or seeded_v2 or seeded_v3 or seeded_eval):
            logger.info("startup: prompts already present")
    except Exception:
        logger.exception("startup: prompt seed failed — admin UI will show 'Not seeded' until resolved")

# Allowed frontend origins
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
]
_frontend_url = os.getenv("FRONTEND_URL", "").strip().rstrip("/")
if _frontend_url:
    ALLOWED_ORIGINS.append(_frontend_url)

# Optional access controls (set via environment to enable)
_ALLOWED_EMAILS = {x.strip().lower() for x in os.getenv("ALLOWED_EMAILS", "").split(",") if x.strip()}
_ALLOWED_DOMAINS = {x.strip().lower().lstrip("@") for x in os.getenv("ALLOWED_DOMAINS", "").split(",") if x.strip()}
_REQUIRED_GROUP = os.getenv("REQUIRED_GROUP", "").strip()

def _user_is_allowed(claims: dict) -> bool:
    """Evaluate optional allowlist/group rules from environment.

    If no rules are set, allow everyone with a valid token.
    """
    # Require group if set
    if _REQUIRED_GROUP:
        groups = claims.get("cognito:groups") or []
        # Accept string or list
        if isinstance(groups, str):
            groups = [groups]
        if _REQUIRED_GROUP not in groups:
            return False

    # If an explicit email allowlist is provided, enforce it strictly
    if _ALLOWED_EMAILS:
        email = (claims.get("email") or "").lower().strip()
        username = (claims.get("username") or claims.get("cognito:username") or "").lower().strip()
        if email and email in _ALLOWED_EMAILS:
            return True
        if username and username in _ALLOWED_EMAILS:
            return True
        return False

    # Otherwise, if domain allowlist is provided, enforce it
    if _ALLOWED_DOMAINS:
        email = (claims.get("email") or "").lower().strip()
        if not email or "@" not in email:
            return False
        domain = email.split("@", 1)[1]
        return domain in _ALLOWED_DOMAINS

    # No rules configured => allow
    return True

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https?://(localhost|127\\.0\\.0\\.1)(:\\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    '''Health check endpoint.'''
    return {"status": "ok"}


@app.get("/api/v1/diagnostics")
def diagnostics():
    """Return runtime diagnostics for optional features (OCR, AI) and core deps.

    This does not throw if deps are missing; instead it reports readiness flags.
    """
    # multipart (required for File/Form)
    multipart_ok = False
    try:
        import multipart  # type: ignore
        multipart_ok = True
    except Exception:
        multipart_ok = False

    # OCR readiness
    ocr_py = False
    try:
        import pytesseract  # type: ignore
        from PIL import Image as _Img  # type: ignore  # noqa: F401
        ocr_py = True
    except Exception:
        ocr_py = False
    tesseract_path = shutil.which("tesseract")
    ocr_enabled = bool(ocr_py and tesseract_path)

    # AI readiness
    api_key_present = bool(os.getenv("OPENAI_API_KEY"))
    openai_ok = False
    try:
        import openai  # type: ignore  # noqa: F401
        openai_ok = True
    except Exception:
        openai_ok = False
    ai_enabled = bool(api_key_present and openai_ok)

    return {
        "status": "ok",
        "multipart": {"installed": multipart_ok},
        "ocr": {
            "pythonDeps": ocr_py,
            "tesseractBinary": bool(tesseract_path),
            "tesseractPath": tesseract_path,
            "enabled": ocr_enabled,
        },
        "ai": {
            "apiKey": api_key_present,
            "sdk": openai_ok,
            "model": os.getenv("OPENAI_MODEL"),
            "enabled": ai_enabled,
        },
    }


def _get_claims_from_auth_header(request: Request):
    verifier = get_default_verifier()
    if not verifier:
        raise HTTPException(status_code=503, detail="Cognito not configured")
    auth = request.headers.get("Authorization")
    token = None
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
    # Optional fallback: allow id_token access via query for debugging the flow
    if not token:
        token = request.query_params.get("id_token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    try:
        claims = verifier.verify(token)
        if not _user_is_allowed(claims):
            raise HTTPException(status_code=403, detail="User not allowed. Please contact the administrator.")
        return claims
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


@app.get("/api/v1/me")
def me(claims: dict = Depends(_get_claims_from_auth_header)):
    return {"claims": claims}

@app.get("/")
def read_root():
    '''Root endpoint.'''
    return {"message": "Hello, World!", "table": TABLE_NAME}

# No explicit startup/shutdown needed for boto3-backed database module

# Simple message entity using single-table pattern
# PK = MSG#demo, SK = WELCOME (static demo example)
PK_CONST = "MSG#demo"
SK_CONST = "WELCOME"

@app.get("/api/message")
def get_message():
    '''Get the demo message.'''
    try:
        response = db.table().get_item(Key={"PK": PK_CONST, "SK": SK_CONST})
    except Exception as e:
        logger.exception("DynamoDB get_item failed")
        raise HTTPException(status_code=500, detail="Internal error") from e
    item = response.get("Item")
    return {"message": item.get("text") if item else "No message found."}

@app.post("/api/message")
async def set_message(request: Request):
    '''Set the demo message. Expects JSON body with {"text": "..."}'''
    data = await request.json()
    text = data.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    item = {
        "PK": PK_CONST,
        "SK": SK_CONST,
        "text": text,
        # Example secondary index attributes (if you want to query messages by type):
        "GSI1PK": "MESSAGE",
        "GSI1SK": f"{PK_CONST}#{SK_CONST}",
    }
    try:
        db.table().put_item(Item=item)
    except Exception as e:
        logger.exception("DynamoDB put_item failed")
        raise HTTPException(status_code=500, detail="Failed to save message") from e
    return {"status": "ok"}


def now_iso() -> str:
    '''Get current time in ISO format.'''
    return datetime.now(timezone.utc).isoformat()


# DynamoDB access is handled by the database module


def create_quiz_session(uid: str, topic_id: str, num_questions: int) -> QuizStartRes:
    '''Create a new quiz session for the user on the given topic.'''
    # database.list_cards_for_topic returns list[dict]; convert to Card models
    card_dicts = list_cards_for_topic(topic_id)
    cards = [Card(**c) for c in card_dicts]
    if not cards:
        raise HTTPException(status_code=404, detail="No cards for topic")
    k = min(num_questions, len(cards))
    selected = random.sample(cards, k)

    # Build MCQs: stem = card.front, correct = card.back, distractors = other backs
    other_backs = [c.back for c in cards]
    questions: List[Question] = []
    for card in selected:
        distractors = [b for b in other_backs if b != card.back]
        distractors = random.sample(distractors, k=min(3, len(distractors)))  # up to 3
        choices = distractors + [card.back]
        random.shuffle(choices)
        correct_idx = choices.index(card.back)
        questions.append(Question(
            id=card.id,
            stem=card.front,
            choices=choices,
            correctIndex=correct_idx,  # Client can ignore this field
        ))

    quiz_id = str(uuid4())
    # Persist session so grading uses the same choices/correctIndex
    save_quiz_session(uid, quiz_id, topic_id, [q.dict() for q in questions])
    return QuizStartRes(quizId=quiz_id, topicId=topic_id, questions=questions)


def load_quiz_session(uid: str, quiz_id: str) -> dict:
    '''Load an existing quiz session for grading.'''
    item = get_quiz_session(uid, quiz_id)
    if not item:
        raise HTTPException(status_code=404, detail="Quiz session not found")
    return item


# =========================
# API v1 routes
# =========================

@app.post("/api/v1/users/bootstrap", response_model=BootstrapRes)
def bootstrap_user(req: BootstrapReq):
    '''Bootstrap user by device ID or create new user.'''
    device_id = req.deviceId
    if device_id:
        existing_uid = get_uid_by_device(device_id)
        if existing_uid:
            return BootstrapRes(uid=existing_uid, isNew=False)
    # Create new user
    uid = str(uuid4())
    put_user_profile(uid, device_id)
    return BootstrapRes(uid=uid, isNew=True)

@app.get("/api/v1/subjects", response_model=List[SubjectWithTopics])
def get_subjects():
    '''List all subjects with their topics.'''
    try:
        grouped = list_topics_grouped()
        return [SubjectWithTopics(subject=g["subject"], topics=[TopicStub(**t) for t in g["topics"]]) for g in grouped]
    except Exception as e:
        logger.exception("Failed to list subjects")
        raise HTTPException(status_code=500, detail="Failed to list subjects") from e

@app.get("/api/v1/topics/{topic_id}/cards", response_model=TopicCardsRes)
def get_topic_cards(topic_id: str):
    '''Get all cards for a given topic ID.'''
    try:
        cards = list_cards_for_topic(topic_id)
        return TopicCardsRes(topicId=topic_id, cards=cards)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get topic cards")
        raise HTTPException(status_code=500, detail="Failed to get topic cards") from e

@app.post("/api/v1/quiz/start", response_model=QuizStartRes)
def quiz_start(req: QuizStartReq):
    # Validate user exists
    if not get_user_profile(req.uid):
        raise HTTPException(status_code=404, detail="User not found")
    try:
        return create_quiz_session(req.uid, req.topicId, req.numQuestions)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to start quiz")
        raise HTTPException(status_code=500, detail="Failed to start quiz") from e

@app.post("/api/v1/quiz/submit", response_model=QuizSubmitRes)
def quiz_submit(req: QuizSubmitReq):
    '''Submit quiz answers and get results.'''
    sess = load_quiz_session(req.uid, req.quizId)
    q_by_id: dict[str, Question] = {}
    for q in sess.get("questions", []):
        # q may be dict; coerce
        q_by_id[q["id"]] = Question(**q)

    breakdown: List[BreakdownItem] = []
    correct_count = 0
    for ans in req.answers:
        q = q_by_id.get(ans.questionId)
        if not q:
            raise HTTPException(status_code=400, detail=f"Unknown questionId {ans.questionId}")
        is_correct = (ans.choiceIndex == (q.correctIndex or 0))
        if is_correct:
            correct_count += 1
        breakdown.append(BreakdownItem(
            questionId=ans.questionId,
            correct=is_correct,
            correctIndex=(q.correctIndex or 0),
            explanation=None
        ))
    score = correct_count

    # Persist final result (serialize Pydantic models to plain dicts for DynamoDB)
    breakdown_dicts = [b.dict() for b in breakdown]
    answers_dicts = [a.dict() for a in req.answers]
    save_quiz_result(
        req.uid,
        req.quizId,
        sess.get("topicId", ""),
        breakdown_dicts,
        score,
        answers_dicts,
    )

    # Optionally delete session (cleanup)
    try:
        delete_quiz_session(req.uid, req.quizId)
    except Exception:
        pass

    # Next steps = revisit wrong answers
    wrong_card_ids = [b.questionId for b in breakdown if not b.correct]
    return QuizSubmitRes(
        score=score,
        breakdown=breakdown,
        nextSteps=NextSteps(cardIds=wrong_card_ids)
    )


@app.get("/api/v1/review/next", response_model=ReviewNextRes)
def review_next(uid: str):
    '''Get next cards for review based on recent wrong answers.'''
    if not get_user_profile(uid):
        raise HTTPException(status_code=404, detail="User not found")
    topic_to_cards = recent_wrong_cards(uid, limit_results=10)
    due_list = [ReviewDueGroup(topicId=t, cardIds=sorted(list(cids))) for t, cids in topic_to_cards.items()]
    # If nothing due, return empty list
    return ReviewNextRes(due=due_list)


# =========================
# Homework submit (OCR + AI help)
# =========================

def _safe_import_tesseract():
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore
        return pytesseract, Image
    except Exception:
        return None, None


def _safe_import_openai():
    try:
        import openai  # type: ignore
        return openai
    except Exception:
        return None


def _safe_import_gcse_help_generator():
    try:
        from gcse_help_generator import GCSEHelpError, GCSEHelpGenerator

        return GCSEHelpGenerator, GCSEHelpError
    except Exception:
        return None, None


def _extract_text_from_image(data_url: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    openai = _safe_import_openai()
    if openai is None:
        raise RuntimeError("openai package not installed")
    if "," in data_url:
        header, b64 = data_url.split(",", 1)
        mime = header.split(":")[1].split(";")[0] if ":" in header else "image/png"
    else:
        b64, mime = data_url, "image/png"
    client = openai.OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Extract the exact text of GCSE exam questions from screenshot images. Return only the question text as it appears. No commentary.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                    {"type": "text", "text": "Extract the GCSE question text from this image."},
                ],
            },
        ],
        max_tokens=1000,
    )
    return (resp.choices[0].message.content or "").strip()


@app.post("/api/v1/homework/submit", response_model=HomeworkSubmitRes)
async def homework_submit(
    uid: str = Form(...),
    question: str = Form(""),
    files: list[UploadFile] = File(default=[])
):
    # Validate uid exists (optional if anonymous allowed)
    if not get_user_profile(uid):
        raise HTTPException(status_code=404, detail="User not found")

    warnings: list[str] = []
    extracted_texts: list[str] = []
    saved_names: list[str] = []

    # OCR using pytesseract if available
    pytesseract, Image = _safe_import_tesseract()
    ocr_enabled = pytesseract is not None and Image is not None
    if not ocr_enabled:
        warnings.append("OCR not available: install pillow and pytesseract for image text extraction.")

    for f in files or []:
        try:
            content = await f.read()
            saved_names.append(f.filename or "uploaded")
            if ocr_enabled and f.content_type and f.content_type.startswith("image/"):
                from io import BytesIO
                try:
                    img = Image.open(BytesIO(content))
                    text = pytesseract.image_to_string(img)
                    if text and text.strip():
                        extracted_texts.append(text.strip())
                except Exception as e:
                    warnings.append(f"OCR failed for {f.filename}: {e}")
            # We could add PDF/text parsing here later
        except Exception as e:
            warnings.append(f"Failed to read file {f.filename}: {e}")

    parts = []
    if question and question.strip():
        parts.append(question.strip())
    parts.extend(extracted_texts)
    combined = "\n\n".join(parts)

    ai_help_text: str | None = None
    if combined.strip():
        # Optional AI assistance via OpenAI if configured
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            openai = _safe_import_openai()
            if openai is None:
                warnings.append("AI help not available: install openai python package.")
            else:
                try:
                    prompt = (
                        "You are a helpful GCSE study assistant. Given the student's question and any OCR-extracted text, "
                        "explain the steps to solve it clearly. If it is a multi-part question, break it down. "
                        "Avoid giving the final answer immediately; guide the student with reasoning and hints.\n\n"
                        f"Student input:\n{combined}\n\nResponse:"
                    )
                    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

                    # Support both new (>=1.0) and legacy (<1.0) SDKs
                    if hasattr(openai, "OpenAI"):
                        # New SDK style
                        client = openai.OpenAI(api_key=openai_api_key)  # type: ignore[attr-defined]
                        resp = client.chat.completions.create(
                            model=model,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.2,
                        )
                        ai_help_text = (resp.choices[0].message.content or "").strip()
                    else:
                        # Legacy SDK style
                        openai.api_key = openai_api_key  # type: ignore[attr-defined]
                        resp = openai.ChatCompletion.create(  # type: ignore[attr-defined]
                            model=model,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.2,
                        )
                        ai_help_text = resp["choices"][0]["message"]["content"].strip()
                except Exception as e:
                    warnings.append(f"AI help failed: {e}")
        else:
            warnings.append("Set OPENAI_API_KEY to enable AI help.")

    return HomeworkSubmitRes(
        extractedText=extracted_texts,
        combinedText=combined,
        aiHelp=ai_help_text,
        files=saved_names,
        warnings=warnings,
    )


@app.post("/api/v1/homework/help-json", response_model=HomeworkHelpJsonRes)
def homework_help_json(req: HomeworkHelpJsonReq):
    # Ensure a profile exists for demo/local flows.
    # The frontend can send `uid="demo"` (or other local UID) before bootstrapping.
    try:
        profile = get_user_profile(req.uid)
    except Exception:
        logger.exception("homework_help_json get_user_profile failed uid=%s", req.uid)
        profile = None

    if not profile:
        # Auto-create for local demo/testing only.
        # In production with auth, this should be handled by bootstrap/signup.
        if req.uid == "demo" or os.getenv("ALLOW_ANONYMOUS_HELP", "").strip().lower() in {"1", "true", "yes"}:
            try:
                # db.put_user_profile signature: (uid, device_id)
                put_user_profile(req.uid, device_id=None)
            except Exception:
                logger.exception("homework_help_json auto-create profile failed uid=%s", req.uid)
        else:
            raise HTTPException(status_code=404, detail="User not found")

    GCSEHelpGenerator, GCSEHelpError = _safe_import_gcse_help_generator()
    if GCSEHelpGenerator is None or GCSEHelpError is None:
        raise HTTPException(
            status_code=500,
            detail="Structured help not available: failed to import generator",
        )

    try:
        gen = GCSEHelpGenerator()
        effective_text = req.text
        if req.image_data_url:
            try:
                extracted = _extract_text_from_image(req.image_data_url)
                if extracted:
                    effective_text = f"{extracted}\n\n{req.text.strip()}".strip() if req.text.strip() else extracted
            except Exception as _e:
                logger.warning("homework_help_json image_extraction_failed: %s", _e)
        result = gen.generate(
            raw_text=effective_text,
            uid=req.uid,
            year_group=req.yearGroup,
            tier=req.tier,
            desired_help_level=req.desiredHelpLevel,
            use_cache=req.useCache,
        )

        problem_id: str | None = None
        attempt_id: str | None = None
        # v2 and v3 both go through the structured-problem storage path —
        # the new ProblemPage navigates by problem_id regardless of which
        # ingestion schema produced the response.
        if result.get("_schema_version") in ("2.0.0", "3.0.0"):
            problem_id = str(uuid4())
            attempt_id = str(uuid4())
            image_s3_key: str | None = None
            if req.image_data_url:
                try:
                    image_s3_key = db.upload_problem_image(problem_id, req.image_data_url)
                except Exception as _e:
                    logger.warning("homework_help_json image_upload_failed: %s", _e)
            db.put_problem(
                problem_id=problem_id,
                user_id=req.uid,
                raw_input=effective_text,
                normalised_form=result.get("normalised_form", effective_text),
                topic_tags=result.get("topic_tags", []),
                difficulty=int(result.get("difficulty", 3)),
                ai_response=result,
                image_s3_key=image_s3_key,
            )
            db.put_attempt(
                attempt_id=attempt_id,
                problem_id=problem_id,
                user_id=req.uid,
            )

        return HomeworkHelpJsonRes(result=result, problem_id=problem_id, attempt_id=attempt_id)
    except GCSEHelpError as e:
        logger.info(
            "homework_help_json bad_request uid=%s error=%s",
            req.uid,
            str(e),
        )
        raise HTTPException(status_code=400, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        # Ensure stack traces make it into .dev-logs/backend.log
        logger.exception(
            "homework_help_json failed uid=%s yearGroup=%s tier=%s",
            req.uid,
            req.yearGroup,
            req.tier,
        )
        raise HTTPException(status_code=500, detail="Help generation failed") from e


# =========================
# Homework: event logging
# =========================
# (The legacy /classify-answer endpoint and its leap-ahead/common-error
# matching logic were removed in Phase 3 — the unified ProblemPage uses
# /homework/evaluate exclusively. See decisions/2026-05-02-phase3-*.md.)


@app.post("/api/v1/homework/log-event", response_model=LogEventRes)
def log_event(req: LogEventReq):
    try:
        db.put_step_event(
            attempt_id=req.attempt_id,
            event_type=req.event_type,
            step_number=req.step_number,
            payload=req.payload or {},
        )
    except Exception:
        logger.exception("log_event failed attempt=%s event=%s", req.attempt_id, req.event_type)
        raise HTTPException(status_code=500, detail="Failed to log event")
    return LogEventRes(ok=True)


# =========================
# Problems & evaluation (phase 1 of the rebuilt engine)
# =========================


@app.get("/api/v1/problems/{problem_id}", response_model=ProblemRes)
def get_problem(problem_id: str):
    """Fetch a stored problem so the new free-mode route can render it.

    The existing /homework/help-json flow returns the AI response inline
    after creation; this endpoint exists so a problem can be loaded later
    by id (e.g. when a route is opened directly, or when the free-mode
    view is reached via a link from elsewhere in the app).
    """
    item = db.get_problem(problem_id)
    if not item:
        raise HTTPException(status_code=404, detail="Problem not found")
    image_url: str | None = None
    if item.get("image_s3_key"):
        try:
            image_url = db.get_problem_image_url(item["image_s3_key"])
        except Exception as _e:
            logger.warning("get_problem presign_failed problem_id=%s: %s", problem_id, _e)
    return ProblemRes(
        problem_id=item["problem_id"],
        user_id=item["user_id"],
        raw_input=item.get("raw_input", ""),
        normalised_form=item.get("normalised_form", ""),
        topic_tags=list(item.get("topic_tags", []) or []),
        difficulty=int(item.get("difficulty", 3)),
        ai_response=dict(item.get("ai_response", {}) or {}),
        created_at=item.get("created_at", ""),
        image_url=image_url,
    )


@app.post("/api/v1/homework/evaluate", response_model=EvaluateRes)
def evaluate(req: EvaluateReq):
    """Evaluate a freeform student submission against a stored problem.

    Cheap-path final-answer match → done. Otherwise call the LLM with the
    admin-managed evaluation prompt and return either markup segments or a
    prose fallback (depending on whether the LLM's segments reconstruct
    the submission character-for-character).
    """
    if not req.submission or not req.submission.strip():
        raise HTTPException(status_code=400, detail="submission is empty")

    if req.mode not in ("free", "guided"):
        raise HTTPException(status_code=400, detail="mode must be 'free' or 'guided'")

    if req.target not in ("main", "simpler"):
        raise HTTPException(status_code=400, detail="target must be 'main' or 'simpler'")

    problem = db.get_problem(req.problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    ai_response = dict(problem.get("ai_response", {}) or {})
    question = ai_response.get("normalised_form") or problem.get("normalised_form") or ""

    from gcse_evaluator import evaluate_submission

    try:
        outcome = evaluate_submission(
            submission=req.submission,
            ai_response=ai_response,
            question=question,
            mode=req.mode,
            target=req.target,
        )
    except Exception:
        logger.exception("evaluate failed attempt=%s problem=%s", req.attempt_id, req.problem_id)
        raise HTTPException(status_code=500, detail="Evaluation failed")

    # Log the attempt. We summarise the segments in the payload rather than
    # storing the full feedback — the full markup can be regenerated from
    # the submission if ever needed for analysis.
    try:
        status_summary = [s.get("status") for s in outcome.segments]
        db.put_step_event(
            attempt_id=req.attempt_id,
            event_type="attempt_submitted",
            step_number=0,  # whole-submission events have no step number
            payload={
                "mode": req.mode,
                "target": req.target,
                "submission": req.submission,
                "is_correct": outcome.is_correct,
                "segment_statuses": status_summary,
                "prose_feedback_used": outcome.prose_feedback is not None,
                "next_prompt_emitted": outcome.next_prompt is not None,
            },
        )
    except Exception:
        logger.exception("evaluate put_step_event failed attempt=%s", req.attempt_id)

    return EvaluateRes(
        is_correct=outcome.is_correct,
        feedback_segments=[FeedbackSegment(**s) for s in outcome.segments],
        prose_feedback=outcome.prose_feedback,
        next_prompt=outcome.next_prompt,
    )


# =========================
# Admin: prompt management
# =========================

_ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "").strip()


def _require_admin(request: Request) -> None:
    if not _ADMIN_API_KEY:
        raise HTTPException(status_code=503, detail="Admin API not configured (ADMIN_API_KEY not set)")
    key = request.headers.get("X-Admin-Key", "")
    if key != _ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")


@app.get("/api/v1/admin/prompts", response_model=List[PromptSummary])
def admin_list_prompts(request: Request):
    _require_admin(request)
    return [PromptSummary(**p) for p in db.list_prompts()]


@app.get("/api/v1/admin/prompts/{prompt_id}/versions", response_model=List[PromptVersion])
def admin_list_versions(prompt_id: str, request: Request):
    _require_admin(request)
    items = db.list_prompt_versions(prompt_id)
    return [PromptVersion(
        promptId=it["promptId"],
        version=int(it["version"]),
        systemPrompt=it["systemPrompt"],
        userPromptTemplate=it["userPromptTemplate"],
        createdAt=it["createdAt"],
        createdBy=it["createdBy"],
        notes=it.get("notes", ""),
    ) for it in items]


@app.get("/api/v1/admin/prompts/{prompt_id}/versions/{version}", response_model=PromptVersion)
def admin_get_version(prompt_id: str, version: int, request: Request):
    _require_admin(request)
    item = db.get_prompt_version(prompt_id, version)
    if not item:
        raise HTTPException(status_code=404, detail="Version not found")
    return PromptVersion(
        promptId=item["promptId"],
        version=int(item["version"]),
        systemPrompt=item["systemPrompt"],
        userPromptTemplate=item["userPromptTemplate"],
        createdAt=item["createdAt"],
        createdBy=item["createdBy"],
        notes=item.get("notes", ""),
    )


@app.put("/api/v1/admin/prompts/{prompt_id}", response_model=PromptSaveRes)
def admin_save_prompt(prompt_id: str, req: PromptSaveReq, request: Request):
    _require_admin(request)
    if prompt_id not in db.KNOWN_PROMPT_IDS:
        raise HTTPException(status_code=400, detail=f"Unknown prompt ID: {prompt_id}")
    new_version = db.put_prompt_version(
        prompt_id,
        system_prompt=req.systemPrompt,
        user_prompt_template=req.userPromptTemplate,
        created_by="admin",
        notes=req.notes,
    )
    # Invalidate in-memory prompt cache in the generator singleton if it exists
    try:
        GCSEHelpGenerator, _ = _safe_import_gcse_help_generator()
        if GCSEHelpGenerator is not None:
            gen = GCSEHelpGenerator()
            gen.reload_prompt()
    except Exception:
        logger.exception("admin_save_prompt reload_prompt failed — will pick up on next generator init")
    return PromptSaveRes(promptId=prompt_id, version=new_version)


@app.get("/api/v1/admin/attempts", response_model=UserAttemptsRes)
def admin_get_attempts(uid: str, days: int = 7, request: Request = None):
    """Return all attempts for a user in the last N days with outcome and max_rung_revealed."""
    _require_admin(request)
    items = db.get_attempts_for_user(uid, days=days)
    return UserAttemptsRes(
        user_id=uid,
        days=days,
        attempts=[
            AttemptSummary(
                attempt_id=it["attempt_id"],
                problem_id=it["problem_id"],
                started_at=it["started_at"],
                outcome=it.get("outcome"),
                max_rung_revealed=int(it.get("max_rung_revealed", 0)),
            )
            for it in items
        ],
    )


@app.post("/api/v1/admin/prompts/{prompt_id}/try", response_model=PromptTryRes)
def admin_try_prompt(prompt_id: str, req: PromptTryReq, request: Request):
    _require_admin(request)
    import time as _time
    from gcse_help_template import create_gcse_help_base_structure
    from gcse_help_prompts import render_user_prompt
    from gcse_help_generator import GCSEHelpGenerator, GCSEHelpError, normalize_exercise_text
    import json as _json

    normalized = normalize_exercise_text(req.testInput)
    if not normalized:
        raise HTTPException(status_code=400, detail="testInput is empty")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY not set")

    base_structure = create_gcse_help_base_structure(
        normalized_text=normalized,
        raw_text=req.testInput,
        schema_version="1.0.0",
        uid="admin-try",
    )
    prompt = render_user_prompt(req.userPromptTemplate, _json.dumps(base_structure, ensure_ascii=False))

    import openai as _openai
    t0 = _time.perf_counter()
    try:
        client = _openai.OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            messages=[
                {"role": "system", "content": req.systemPrompt},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=2500,
        )
        result = _json.loads(resp.choices[0].message.content or "{}")
    except Exception as e:
        logger.exception("admin_try_prompt llm_call_failed")
        raise HTTPException(status_code=500, detail=f"LLM call failed: {e}") from e

    duration_ms = int((_time.perf_counter() - t0) * 1000)
    active = db.get_prompt_active(prompt_id)
    prompt_version = int(active["version"]) if active else 0
    return PromptTryRes(result=result, promptVersion=prompt_version, durationMs=duration_ms)


@app.post("/api/v1/progress", response_model=schemas.ProgressItem)
def update_progress(req: schemas.ProgressUpdateReq, p = Depends(get_current_principal)):
    if not p:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    saved = db.save_progress(p.sub, req.dict())
    return schemas.ProgressItem(
        topicId=saved["topicId"],
        exerciseId=saved["exerciseId"],
        status=saved["status"],
        score=saved.get("score"),
        updatedAt=datetime.fromtimestamp(saved["updatedAt"], tz=timezone.utc),
    )

@app.get("/api/v1/progress", response_model=schemas.ProgressGetRes)
def list_progress(topicId: str | None = None, p = Depends(get_current_principal)):
    if not p:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    items = db.get_progress(p.sub, topicId)
    return schemas.ProgressGetRes(items=[
        schemas.ProgressItem(
            topicId=i["topicId"],
            exerciseId=i["exerciseId"],
            status=i["status"],
            score=i.get("score"),
            updatedAt=datetime.fromtimestamp(i["updatedAt"], tz=timezone.utc),
        ) for i in items
    ])


