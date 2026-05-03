from enum import Enum
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


class HomeworkHelpJsonReq(BaseModel):
    '''Request schema for generating structured help JSON.'''
    uid: str
    text: str
    yearGroup: int | None = 9
    tier: str = "unknown"
    desiredHelpLevel: str = "auto"
    useCache: bool = True


class HomeworkHelpJsonRes(BaseModel):
    '''Response schema for structured help JSON generation.'''
    result: Dict[str, Any]
    problem_id: Optional[str] = None
    attempt_id: Optional[str] = None


class LogEventReq(BaseModel):
    '''Request schema for logging a step event.'''
    attempt_id: str
    event_type: str
    step_number: int
    payload: Optional[Dict[str, Any]] = None


class LogEventRes(BaseModel):
    ok: bool


# ── Markup-feedback evaluation (phase 1 of the rebuilt engine) ──────────────


class FeedbackSegment(BaseModel):
    '''One segment of the student's submission, marked up by the evaluator.

    Concatenating segment.text in order must equal the original submission
    character-for-character — this is enforced before the response is sent
    so the frontend can render aligned markup with confidence.
    '''
    text: str
    # correct | incomplete | wrong | unclear
    status: str
    # Short explanation directed at the student. Null for routine "yes that's
    # right" cases on correct segments where no comment adds value.
    comment: Optional[str] = None


class EvaluateReq(BaseModel):
    '''Request schema for evaluating a freeform student submission.

    `mode` controls whether the evaluator suggests a next prompt for the
    student. In "guided" mode the response includes next_prompt; in "free"
    mode the system stays out of the way and only marks up what was written.
    Default is "free" for backwards compatibility with phase-1 callers.

    `target` selects which canonical solution the submission is evaluated
    against: "main" (the original problem) or "simpler" (the slim warm-up
    variant stored on the Exercise via simpler_version). Default "main".
    '''
    attempt_id: str
    problem_id: str
    submission: str
    mode: str = "free"  # "free" | "guided"
    target: str = "main"  # "main" | "simpler"


class EvaluateRes(BaseModel):
    '''Response schema for evaluation.

    On a cheap-path final-answer match: is_correct=True, no segments emitted —
    the frontend renders a success state.

    On the LLM path: is_correct=False (still working), feedback_segments
    populated. If markup validation failed, prose_feedback carries a plain
    string and feedback_segments stays empty.

    next_prompt is populated only in guided mode, on the LLM path. It's a
    short tutor-style suggestion for the student's next move.
    '''
    is_correct: bool
    feedback_segments: List[FeedbackSegment] = []
    prose_feedback: Optional[str] = None
    next_prompt: Optional[str] = None


class ProblemRes(BaseModel):
    '''Response schema for fetching a stored problem by id.

    Returns the canonical AI response payload (v2 shape) plus ownership and
    metadata, so the frontend can render the problem and use the canonical
    solution + milestones for the evaluation flow.
    '''
    problem_id: str
    user_id: str
    raw_input: str
    normalised_form: str
    topic_tags: List[str]
    difficulty: int
    ai_response: Dict[str, Any]
    created_at: str

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


# Admin: prompt management
class PromptSummary(BaseModel):
    promptId: str
    activeVersion: Optional[int]
    updatedAt: Optional[str]

class PromptVersion(BaseModel):
    promptId: str
    version: int
    systemPrompt: str
    userPromptTemplate: str
    createdAt: str
    createdBy: str
    notes: str

class PromptSaveReq(BaseModel):
    systemPrompt: str
    userPromptTemplate: str
    notes: str = ""

class PromptSaveRes(BaseModel):
    promptId: str
    version: int

class PromptTryReq(BaseModel):
    systemPrompt: str
    userPromptTemplate: str
    testInput: str

class PromptTryRes(BaseModel):
    result: Dict[str, Any]
    promptVersion: int
    durationMs: int


# ── Problems, Attempts, Step Events (Ticket 1.4) ──────────────────────────

class AttemptOutcome(str, Enum):
    solved_unaided = "solved_unaided"
    solved_with_hints = "solved_with_hints"
    revealed_full_solution = "revealed_full_solution"
    abandoned = "abandoned"


class StepEventType(str, Enum):
    attempt_submitted = "attempt_submitted"
    rung_revealed = "rung_revealed"
    step_completed = "step_completed"
    hint_dismissed_before_answer = "hint_dismissed_before_answer"


class AttemptSummary(BaseModel):
    attempt_id: str
    problem_id: str
    started_at: str
    outcome: Optional[str] = None
    max_rung_revealed: int = 0


class UserAttemptsRes(BaseModel):
    user_id: str
    days: int
    attempts: List[AttemptSummary]

