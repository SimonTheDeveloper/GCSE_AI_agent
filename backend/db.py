import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, List, Dict
from uuid import uuid4

import boto3
from boto3.dynamodb.conditions import Key

AWS_REGION = os.getenv("AWS_REGION") or "eu-west-1"
TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "gcse_app")
ENDPOINT_URL = os.getenv("DYNAMODB_ENDPOINT_URL")  # optional local endpoint

_dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION, endpoint_url=ENDPOINT_URL)
_table = _dynamodb.Table(TABLE_NAME)

GSI1_NAME = os.getenv("DYNAMODB_GSI1", "GSI1")
GSI2_NAME = os.getenv("DYNAMODB_GSI2", "GSI2")


def table():
    return _table


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _query_all(**kwargs) -> List[dict]:
    items: List[dict] = []
    resp = _table.query(**kwargs)
    items.extend(resp.get("Items", []))
    while "LastEvaluatedKey" in resp:
        resp = _table.query(ExclusiveStartKey=resp["LastEvaluatedKey"], **kwargs)
        items.extend(resp.get("Items", []))
    return items


# Users
def get_user_profile(uid: str) -> dict | None:
    r = _table.get_item(Key={"PK": f"USER#{uid}", "SK": "PROFILE"})
    return r.get("Item")


def put_user_profile(uid: str, device_id: str | None) -> None:
    _table.put_item(Item={
        "PK": f"USER#{uid}",
        "SK": "PROFILE",
        "Type": "User",
        "deviceId": device_id,
        "createdAt": now_iso(),
    })
    if device_id:
        _table.put_item(Item={
            "PK": f"DEVICE#{device_id}",
            "SK": "USER_LINK",
            "Type": "DeviceLink",
            "uid": uid,
            "linkedAt": now_iso(),
        })


def get_uid_by_device(device_id: str) -> str | None:
    r = _table.get_item(Key={"PK": f"DEVICE#{device_id}", "SK": "USER_LINK"})
    item = r.get("Item")
    return item.get("uid") if item else None


# Topics and cards
def list_topics_grouped() -> List[dict]:
    items = _query_all(
        IndexName=GSI1_NAME,
        KeyConditionExpression=Key("GSI1PK").eq("TOPIC_LIST")
    )
    subjects: Dict[str, List[dict]] = {}
    for it in items:
        if it.get("Type") != "TopicMeta":
            continue
        subject = it["subject"]
        topic_id = it["SK"].split("#", 1)[-1]
        subjects.setdefault(subject, []).append({
            "id": topic_id,
            "title": it.get("title", topic_id),
            "estMinutes": int(it.get("estMinutes", it.get("estimatedMinutes", 10))),
        })
    out = [{"subject": s, "topics": sorted(ts, key=lambda x: x["title"].lower())}
           for s, ts in subjects.items()]
    out.sort(key=lambda x: x["subject"].lower())
    return out


def list_cards_for_topic(topic_id: str) -> List[dict]:
    items = _query_all(
        IndexName=GSI1_NAME,
        KeyConditionExpression=Key("GSI1PK").eq(f"TOPIC#{topic_id}") & Key("GSI1SK").begins_with("CARD#")
    )
    cards: List[dict] = []
    for it in items:
        if it.get("Type") != "RevCard":
            continue
        card_id = it["SK"].split("#", 1)[-1]
        cards.append({
            "id": card_id,
            "front": it.get("front", ""),
            "back": it.get("back", ""),
            "tag": it.get("difficultyTag"),
        })
    return cards


# Quiz sessions/results
def save_quiz_session(uid: str, quiz_id: str, topic_id: str, questions: List[dict]) -> None:
    _table.put_item(Item={
        "PK": f"USER#{uid}",
        "SK": f"QUIZ#{quiz_id}#SESSION",
        "Type": "QuizSession",
        "topicId": topic_id,
        "createdAt": now_iso(),
        "questions": questions,
        "GSI1PK": f"QUIZ#{quiz_id}",
        "GSI1SK": f"USER#{uid}",
    })


def get_quiz_session(uid: str, quiz_id: str) -> dict | None:
    r = _table.get_item(Key={"PK": f"USER#{uid}", "SK": f"QUIZ#{quiz_id}#SESSION"})
    return r.get("Item")


def delete_quiz_session(uid: str, quiz_id: str) -> None:
    _table.delete_item(Key={"PK": f"USER#{uid}", "SK": f"QUIZ#{quiz_id}#SESSION"})


def save_quiz_result(uid: str, quiz_id: str, topic_id: str,
                     breakdown: List[dict], score: int, answers: List[dict]) -> None:
    _table.put_item(Item={
        "PK": f"USER#{uid}",
        "SK": f"QUIZ#{quiz_id}",
        "Type": "QuizResult",
        "topicId": topic_id,
        "completedAt": now_iso(),
        "score": score,
        "breakdown": breakdown,
        "answers": answers,
        "GSI1PK": f"QUIZ#{quiz_id}",
        "GSI1SK": f"USER#{uid}",
    })


def recent_wrong_cards(uid: str, limit_results: int = 10) -> Dict[str, set]:
    resp = _table.query(
        KeyConditionExpression=Key("PK").eq(f"USER#{uid}") & Key("SK").begins_with("QUIZ#"),
        ScanIndexForward=False,
        Limit=limit_results,
    )
    topic_to_cards: Dict[str, set] = {}
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

# Prompts
KNOWN_PROMPT_IDS = ["ingestion", "similar", "score", "classify"]


def _prompt_version_sk(version: int) -> str:
    return f"VERSION#{version:04d}"


def get_prompt_active(prompt_id: str) -> dict | None:
    """Return the active pointer record for a prompt, or None if not seeded."""
    r = _table.get_item(Key={"PK": f"PROMPT#{prompt_id}", "SK": "ACTIVE"})
    return r.get("Item")


def get_prompt_version(prompt_id: str, version: int) -> dict | None:
    r = _table.get_item(Key={"PK": f"PROMPT#{prompt_id}", "SK": _prompt_version_sk(version)})
    return r.get("Item")


def list_prompt_versions(prompt_id: str) -> list[dict]:
    items = _query_all(
        KeyConditionExpression=Key("PK").eq(f"PROMPT#{prompt_id}") & Key("SK").begins_with("VERSION#")
    )
    return sorted(items, key=lambda x: x["SK"])


def put_prompt_version(
    prompt_id: str,
    *,
    system_prompt: str,
    user_prompt_template: str,
    created_by: str,
    notes: str = "",
) -> int:
    """Write a new version record and set it as active. Returns the new version number."""
    existing = list_prompt_versions(prompt_id)
    new_version = len(existing) + 1

    _table.put_item(Item={
        "PK": f"PROMPT#{prompt_id}",
        "SK": _prompt_version_sk(new_version),
        "Type": "PromptVersion",
        "promptId": prompt_id,
        "version": new_version,
        "systemPrompt": system_prompt,
        "userPromptTemplate": user_prompt_template,
        "createdAt": now_iso(),
        "createdBy": created_by,
        "notes": notes,
    })
    _table.put_item(Item={
        "PK": f"PROMPT#{prompt_id}",
        "SK": "ACTIVE",
        "Type": "PromptActive",
        "promptId": prompt_id,
        "version": new_version,
        "updatedAt": now_iso(),
    })
    return new_version


def list_prompts() -> list[dict]:
    """Return the active-pointer record for every known prompt ID."""
    results = []
    for prompt_id in KNOWN_PROMPT_IDS:
        active = get_prompt_active(prompt_id)
        results.append({
            "promptId": prompt_id,
            "activeVersion": active["version"] if active else None,
            "updatedAt": active["updatedAt"] if active else None,
        })
    return results


# Progress helpers
def save_progress(user_id: str, item: dict) -> dict:
    import time as _time
    now = int(_time.time())
    pk = f"USER#{user_id}"
    sk = f"PROGRESS#{item['topicId']}#{item['exerciseId']}"
    put = {
        "PK": pk,
        "SK": sk,
        "Type": "Progress",
        "topicId": item["topicId"],
        "exerciseId": item["exerciseId"],
        "status": item.get("status", "unknown"),
        "score": item.get("score"),
        "meta": item.get("meta"),
        "updatedAt": now,
        "GSI1PK": f"PROGRESS#{item['topicId']}",
        "GSI1SK": now,
    }
    _table.put_item(Item=put)
    return put

def get_progress(user_id: str, topic_id: str | None = None) -> list[dict]:
    pk = f"USER#{user_id}"
    if topic_id:
        prefix = f"PROGRESS#{topic_id}#"
        resp = _table.query(
            KeyConditionExpression=Key("PK").eq(pk) & Key("SK").begins_with(prefix)
        )
    else:
        resp = _table.query(
            KeyConditionExpression=Key("PK").eq(pk) & Key("SK").begins_with("PROGRESS#")
        )
    return resp.get("Items", [])


# ── Utility ───────────────────────────────────────────────────────────────

def _floats_to_decimal(obj: Any) -> Any:
    """DynamoDB doesn't accept Python floats; convert them to Decimal."""
    if isinstance(obj, list):
        return [_floats_to_decimal(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _floats_to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, float):
        return Decimal(str(obj))
    return obj


# ── Problems ──────────────────────────────────────────────────────────────

def put_problem(
    *,
    problem_id: str,
    user_id: str,
    raw_input: str,
    normalised_form: str,
    topic_tags: List[str],
    difficulty: int,
    ai_response: dict,
) -> dict:
    item: Dict[str, Any] = {
        "PK": f"PROBLEM#{problem_id}",
        "SK": "METADATA",
        "Type": "Problem",
        "schema_version": 2,
        "problem_id": problem_id,
        "user_id": user_id,
        "created_at": now_iso(),
        "raw_input": raw_input,
        "normalised_form": normalised_form,
        "topic_tags": topic_tags,
        "difficulty": difficulty,
        "ai_response": _floats_to_decimal(ai_response),
        # GSI2: latest attempt for this problem by this user
        "GSI2PK": f"PROBLEM#{problem_id}#USER#{user_id}",
    }
    _table.put_item(Item=item)
    return item


def get_problem(problem_id: str) -> dict | None:
    r = _table.get_item(Key={"PK": f"PROBLEM#{problem_id}", "SK": "METADATA"})
    return r.get("Item")


# ── Attempts ──────────────────────────────────────────────────────────────

def put_attempt(*, attempt_id: str, problem_id: str, user_id: str) -> dict:
    started_at = now_iso()
    item: Dict[str, Any] = {
        "PK": f"ATTEMPT#{attempt_id}",
        "SK": "METADATA",
        "Type": "Attempt",
        "attempt_id": attempt_id,
        "problem_id": problem_id,
        "user_id": user_id,
        "started_at": started_at,
        "completed_at": None,
        "outcome": None,
        "max_rung_revealed": 0,
        "active_time_seconds": None,
        "self_recovered": False,
        "explanation_text": None,
        "explanation_rubric": None,
        # GSI1: all attempts for a user, sorted by time
        "GSI1PK": f"USER_ATTEMPTS#{user_id}",
        "GSI1SK": f"ATTEMPT#{started_at}",
        # GSI2: latest attempt for a specific problem by this user
        "GSI2PK": f"PROBLEM#{problem_id}#USER#{user_id}",
        "GSI2SK": f"ATTEMPT#{started_at}",
    }
    _table.put_item(Item=item)
    return item


def update_attempt(attempt_id: str, **fields: Any) -> None:
    """Partial update — only the supplied fields are written."""
    if not fields:
        return
    names: Dict[str, str] = {}
    values: Dict[str, Any] = {}
    set_parts: List[str] = []
    remove_parts: List[str] = []
    for i, (k, v) in enumerate(fields.items()):
        name_token = f"#f{i}"
        names[name_token] = k
        if v is None:
            remove_parts.append(name_token)
        else:
            val_token = f":v{i}"
            values[val_token] = v
            set_parts.append(f"{name_token} = {val_token}")

    expression_parts = []
    if set_parts:
        expression_parts.append("SET " + ", ".join(set_parts))
    if remove_parts:
        expression_parts.append("REMOVE " + ", ".join(remove_parts))

    kwargs: Dict[str, Any] = {
        "Key": {"PK": f"ATTEMPT#{attempt_id}", "SK": "METADATA"},
        "UpdateExpression": " ".join(expression_parts),
        "ExpressionAttributeNames": names,
    }
    if values:
        kwargs["ExpressionAttributeValues"] = values
    _table.update_item(**kwargs)


def get_attempt(attempt_id: str) -> dict | None:
    r = _table.get_item(Key={"PK": f"ATTEMPT#{attempt_id}", "SK": "METADATA"})
    return r.get("Item")


def get_attempts_for_user(user_id: str, days: int = 7) -> List[dict]:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    return _query_all(
        IndexName=GSI1_NAME,
        KeyConditionExpression=(
            Key("GSI1PK").eq(f"USER_ATTEMPTS#{user_id}") &
            Key("GSI1SK").gte(f"ATTEMPT#{cutoff}")
        ),
        ScanIndexForward=False,
    )


def get_latest_attempt_for_problem(problem_id: str, user_id: str) -> dict | None:
    resp = _table.query(
        IndexName=GSI2_NAME,
        KeyConditionExpression=Key("GSI2PK").eq(f"PROBLEM#{problem_id}#USER#{user_id}"),
        ScanIndexForward=False,
        Limit=1,
    )
    items = resp.get("Items", [])
    return items[0] if items else None


# ── Step events ───────────────────────────────────────────────────────────

def put_step_event(
    *,
    attempt_id: str,
    event_type: str,
    step_number: int,
    payload: dict,
) -> dict:
    event_id = str(uuid4())
    created_at = now_iso()
    item: Dict[str, Any] = {
        "PK": f"ATTEMPT#{attempt_id}",
        "SK": f"EVENT#{created_at}#{event_id}",
        "Type": "StepEvent",
        "event_id": event_id,
        "attempt_id": attempt_id,
        "event_type": event_type,
        "step_number": step_number,
        "created_at": created_at,
        "payload": payload,
    }
    _table.put_item(Item=item)
    return item


def get_step_events_for_attempt(attempt_id: str) -> List[dict]:
    return _query_all(
        KeyConditionExpression=(
            Key("PK").eq(f"ATTEMPT#{attempt_id}") &
            Key("SK").begins_with("EVENT#")
        ),
    )
