from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime


class BootstrapReq(BaseModel):
    '''Request schema for bootstrapping the app'''
    deviceId: str | None = None

class BootstrapRes(BaseModel):
    '''Response schema for bootstrapping the app'''
    uid: str
    isNew: bool

class TopicStub(BaseModel):
    '''A brief representation of a topic'''
    id: str
    title: str
    estMinutes: int

class SubjectWithTopics(BaseModel):
    '''A subject and its associated topics'''
    subject: str
    topics: List[TopicStub]

class Card(BaseModel):
    '''A revision card'''
    id: str
    front: str
    back: str
    tag: str | None = None

class TopicCardsRes(BaseModel):
    '''Response schema for fetching cards of a topic'''
    topicId: str
    cards: List[Card]

class QuizStartReq(BaseModel):
    '''Request schema for starting a quiz'''
    uid: str
    topicId: str
    numQuestions: int = 5

class Question(BaseModel):
    '''A quiz question'''
    id: str
    stem: str
    choices: List[str]
    correctIndex: int | None = None  # omit on client if desired

class QuizStartRes(BaseModel):
    '''Response schema for starting a quiz'''
    quizId: str
    topicId: str
    questions: List[Question]

class Answer(BaseModel):
    '''An answer to a quiz question'''
    questionId: str
    choiceIndex: int

class QuizSubmitReq(BaseModel):
    '''Request schema for submitting a quiz'''
    uid: str
    quizId: str
    answers: List[Answer]

class BreakdownItem(BaseModel):
    '''Breakdown of a quiz question result'''
    questionId: str
    correct: bool
    correctIndex: int
    explanation: str | None = None

class NextSteps(BaseModel):
    '''Next steps after a quiz'''
    cardIds: List[str]

class QuizSubmitRes(BaseModel):
    '''Response schema after submitting a quiz'''
    score: int
    breakdown: List[BreakdownItem]
    nextSteps: NextSteps

class ReviewDueGroup(BaseModel):
    '''A group of cards due for review in a topic'''
    topicId: str
    cardIds: List[str]

class ReviewNextRes(BaseModel):
    '''Response schema for fetching next review cards'''
    due: List[ReviewDueGroup]


# Homework
class HomeworkSubmitRes(BaseModel):
    '''Response schema after submitting homework'''
    extractedText: List[str]
    combinedText: str
    aiHelp: str | None = None
    files: List[str] = []
    warnings: List[str] = []

class ProgressUpdateReq(BaseModel):
    topicId: str
    exerciseId: str
    status: str  # e.g., "started" | "completed" | "correct" | "incorrect"
    score: Optional[float] = None
    meta: Optional[Dict[str, Any]] = None
    occurredAt: Optional[datetime] = None  # optional client timestamp

class ProgressItem(BaseModel):
    topicId: str
    exerciseId: str
    status: str
    score: Optional[float] = None
    updatedAt: datetime

class ProgressGetRes(BaseModel):
    items: List[ProgressItem]

