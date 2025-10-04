from typing import List
from pydantic import BaseModel


class BootstrapReq(BaseModel):
    deviceId: str | None = None

class BootstrapRes(BaseModel):
    uid: str
    isNew: bool

class TopicStub(BaseModel):
    id: str
    title: str
    estMinutes: int

class SubjectWithTopics(BaseModel):
    subject: str
    topics: List[TopicStub]

class Card(BaseModel):
    id: str
    front: str
    back: str
    tag: str | None = None

class TopicCardsRes(BaseModel):
    topicId: str
    cards: List[Card]

class QuizStartReq(BaseModel):
    uid: str
    topicId: str
    numQuestions: int = 5

class Question(BaseModel):
    id: str
    stem: str
    choices: List[str]
    correctIndex: int | None = None  # omit on client if desired

class QuizStartRes(BaseModel):
    quizId: str
    topicId: str
    questions: List[Question]

class Answer(BaseModel):
    questionId: str
    choiceIndex: int

class QuizSubmitReq(BaseModel):
    uid: str
    quizId: str
    answers: List[Answer]

class BreakdownItem(BaseModel):
    questionId: str
    correct: bool
    correctIndex: int
    explanation: str | None = None

class NextSteps(BaseModel):
    cardIds: List[str]

class QuizSubmitRes(BaseModel):
    score: int
    breakdown: List[BreakdownItem]
    nextSteps: NextSteps

class ReviewDueGroup(BaseModel):
    topicId: str
    cardIds: List[str]

class ReviewNextRes(BaseModel):
    due: List[ReviewDueGroup]

