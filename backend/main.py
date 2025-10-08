import logging
import os
import random
from datetime import datetime, timezone
from typing import List
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
                        HomeworkSubmitRes)



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "gcse_app")
GSI1_NAME = os.getenv("DYNAMODB_GSI1", "GSI1")

app = FastAPI()

# Allowed frontend origins (add others if needed)
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
]

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


@app.post("/api/v1/homework/submit", response_model=HomeworkSubmitRes)
async def homework_submit(
    uid: str = Form(...),
    question: str = Form(""),
    files: list[UploadFile] = File(default_factory=list),
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


