import os
from datetime import datetime, timezone
from typing import List, Dict

import boto3
from boto3.dynamodb.conditions import Key

AWS_REGION = os.getenv("AWS_REGION") or "eu-west-1"
TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "gcse_app")
ENDPOINT_URL = os.getenv("DYNAMODB_ENDPOINT_URL")  # optional local endpoint

_dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION, endpoint_url=ENDPOINT_URL)
_table = _dynamodb.Table(TABLE_NAME)

GSI1_NAME = os.getenv("DYNAMODB_GSI1", "GSI1")


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
