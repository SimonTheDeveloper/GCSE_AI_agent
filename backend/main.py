import logging
import os
import random
from datetime import datetime, timezone
from typing import List
from uuid import uuid4
from dotenv import load_dotenv
import db

from db import (
    get_user_profile, put_user_profile, get_uid_by_device,
    list_topics_grouped, list_cards_for_topic,
    save_quiz_session, get_quiz_session, delete_quiz_session,
    save_quiz_result, recent_wrong_cards,
)

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from schemas import (BootstrapReq, BootstrapRes, BreakdownItem, Card,
                        NextSteps, Question, QuizStartReq, QuizStartRes, QuizSubmitReq,
                        QuizSubmitRes, ReviewDueGroup, ReviewNextRes,
                        SubjectWithTopics, TopicCardsRes, TopicStub, Answer)


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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    '''Health check endpoint.'''
    return {"status": "ok"}

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

    # Persist final result
    save_quiz_result(req.uid, req.quizId, sess.get("topicId", ""), breakdown, score, req.answers)

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


