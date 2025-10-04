import logging
import os
import random
from datetime import datetime, timezone
from typing import List
from uuid import uuid4
from dotenv import load_dotenv
import boto3
import database

from boto3.dynamodb.conditions import Key

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

# Initialize a session using Amazon DynamoDB (credentials resolved by task role in ECS)
session = boto3.Session(region_name=AWS_REGION)

# Initialize DynamoDB resource (allow optional local override)
endpoint_override = os.getenv("DYNAMODB_ENDPOINT_URL")
dynamodb = session.resource('dynamodb', endpoint_url=endpoint_override) if endpoint_override else session.resource('dynamodb')

# Reference the DynamoDB table
try:
    table = dynamodb.Table(TABLE_NAME)
except Exception as e:
    logger.error(f"Failed to reference table {TABLE_NAME}: {e}")
    raise

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

@app.on_event("startup")
async def startup():
    '''Startup event to connect to the database.'''
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    '''Shutdown event to disconnect from the database.'''
    await database.disconnect()

# Simple message entity using single-table pattern
# PK = MSG#demo, SK = WELCOME (static demo example)
PK_CONST = "MSG#demo"
SK_CONST = "WELCOME"

@app.get("/api/message")
def get_message():
    '''Get the demo message.'''
    try:
        response = table.get_item(Key={"PK": PK_CONST, "SK": SK_CONST})
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
        table.put_item(Item=item)
    except Exception as e:
        logger.exception("DynamoDB put_item failed")
        raise HTTPException(status_code=500, detail="Failed to save message") from e
    return {"status": "ok"}


def now_iso() -> str:
    '''Get current time in ISO format.'''
    return datetime.now(timezone.utc).isoformat()


def ddb_query_all(**kwargs) -> List[dict]:
    '''Helper to perform DynamoDB query and handle pagination, returning all items.'''
    items: List[dict] = []
    resp = table.query(**kwargs)
    items.extend(resp.get("Items", []))
    while "LastEvaluatedKey" in resp:
        resp = table.query(ExclusiveStartKey=resp["LastEvaluatedKey"], **kwargs)
        items.extend(resp.get("Items", []))
    return items

def get_user_profile(uid: str) -> dict | None:
    '''Fetch user profile by uid.'''
    r = table.get_item(Key={"PK": f"USER#{uid}", "SK": "PROFILE"})
    return r.get("Item")

def put_user_profile(uid: str, device_id: str | None) -> None:
    '''Create user profile and optionally link device ID.'''
    table.put_item(Item={
        "PK": f"USER#{uid}",
        "SK": "PROFILE",
        "Type": "User",
        "deviceId": device_id,
        "createdAt": now_iso(),
    })
    if device_id:
        # Link device -> user for future bootstrap lookups
        table.put_item(Item={
            "PK": f"DEVICE#{device_id}",
            "SK": "USER_LINK",
            "Type": "DeviceLink",
            "uid": uid,
            "linkedAt": now_iso(),
        })

def get_uid_by_device(device_id: str) -> str | None:
    '''Lookup uid by device ID.'''
    r = table.get_item(Key={"PK": f"DEVICE#{device_id}", "SK": "USER_LINK"})
    item = r.get("Item")
    return item.get("uid") if item else None


def list_all_topics_grouped() -> List[SubjectWithTopics]:
    '''List all topics grouped by subject.'''
    # TopicMeta items are on GSI1 with:
    #   GSI1PK = "TOPIC_LIST", GSI1SK = "<subject>#<sort>"
    items = ddb_query_all(
        IndexName=GSI1_NAME,
        KeyConditionExpression=Key("GSI1PK").eq("TOPIC_LIST")
    )
    subjects: dict[str, List[TopicStub]] = {}
    for it in items:
        if it.get("Type") != "TopicMeta":
            continue
        subject = it["subject"]
        topic_id = it["SK"].split("#", 1)[-1]  # SK = "TOPIC#<topicId>"
        subjects.setdefault(subject, []).append(TopicStub(
            id=topic_id,
            title=it.get("title", topic_id),
            estMinutes=int(it.get("estMinutes", it.get("estimatedMinutes", 10)))
        ))
    # Optional: keep deterministic order
    out = []
    for subject, topics in subjects.items():
        topics.sort(key=lambda t: t.title.lower())
        out.append(SubjectWithTopics(subject=subject, topics=topics))
    out.sort(key=lambda s: s.subject.lower())
    return out


def list_cards_for_topic(topic_id: str) -> List[Card]:
    '''List all cards for a given topic ID.'''
    # RevCard: PK=CONTENT#<topicId>, SK=CARD#<cardId>
    # Also on GSI1: GSI1PK=TOPIC#<topicId>, GSI1SK=CARD#<cardId>
    items = ddb_query_all(
        IndexName=GSI1_NAME,
        KeyConditionExpression=Key("GSI1PK").eq(f"TOPIC#{topic_id}") & Key("GSI1SK").begins_with("CARD#")
    )
    cards: List[Card] = []
    for it in items:
        if it.get("Type") != "RevCard":
            continue
        card_id = it["SK"].split("#", 1)[-1]
        cards.append(Card(
            id=card_id,
            front=it.get("front", ""),
            back=it.get("back", ""),
            tag=it.get("difficultyTag")
        ))
    return cards

def create_quiz_session(uid: str, topic_id: str, num_questions: int) -> QuizStartRes:
    '''Create a new quiz session for the user on the given topic.'''
    cards = list_cards_for_topic(topic_id)
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
    session_item = {
        "PK": f"USER#{uid}",
        "SK": f"QUIZ#{quiz_id}#SESSION",
        "Type": "QuizSession",
        "topicId": topic_id,
        "createdAt": now_iso(),
        # Pydantic v1 compatibility: use .dict() instead of .model_dump()
        "questions": [q.dict() for q in questions],
        "GSI1PK": f"QUIZ#{quiz_id}",
        "GSI1SK": f"USER#{uid}",
    }
    table.put_item(Item=session_item)
    return QuizStartRes(quizId=quiz_id, topicId=topic_id, questions=questions)


def load_quiz_session(uid: str, quiz_id: str) -> dict:
    '''Load an existing quiz session for grading.'''
    r = table.get_item(Key={"PK": f"USER#{uid}", "SK": f"QUIZ#{quiz_id}#SESSION"})
    item = r.get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="Quiz session not found")
    return item

def save_quiz_result(uid: str, quiz_id: str, topic_id: str, breakdown: List[BreakdownItem], score: int, answers: List[Answer]) -> None:
    '''Save the final quiz result.'''
    item = {
        "PK": f"USER#{uid}",
        "SK": f"QUIZ#{quiz_id}",
        "Type": "QuizResult",
        "topicId": topic_id,
        "completedAt": now_iso(),
        "score": score,
        # Pydantic v1 compatibility: use .dict()
        "breakdown": [b.dict() for b in breakdown],
        "answers": [a.dict() for a in answers],
        "GSI1PK": f"QUIZ#{quiz_id}",
        "GSI1SK": f"USER#{uid}",
    }
    table.put_item(Item=item)

def recent_wrong_cards(uid: str, limit_results: int = 10) -> dict[str, set[str]]:
    '''Fetch recent quiz results and return a mapping of topicId -> set of cardIds that were answered incorrectly.'''
    # Query recent quiz results by SK prefix
    resp = table.query(
        KeyConditionExpression=Key("PK").eq(f"USER#{uid}") & Key("SK").begins_with("QUIZ#"),
        ScanIndexForward=False,  # newest first
        Limit=limit_results
    )
    topic_to_cards: dict[str, set[str]] = {}
    for it in resp.get("Items", []):
        if it.get("Type") != "QuizResult":
            continue
        topic_id = it.get("topicId")
        for b in it.get("breakdown", []):
            if not b.get("correct"):
                qid = b.get("questionId")
                if topic_id and qid:
                    topic_to_cards.setdefault(topic_id, set()).add(qid)
    return topic_to_cards

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
        return list_all_topics_grouped()
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
        table.delete_item(Key={"PK": f"USER#{req.uid}", "SK": f"QUIZ#{req.quizId}#SESSION"})
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


