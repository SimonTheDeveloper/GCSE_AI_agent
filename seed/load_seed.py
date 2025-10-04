#!/usr/bin/env python3
import os
import json
import sys
from pathlib import Path
from typing import Any

import boto3

TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "gcse_app")
AWS_REGION = os.environ.get("AWS_REGION")
DDB_ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT_URL")

session = boto3.Session(region_name=AWS_REGION)
if DDB_ENDPOINT:
    ddb = session.resource("dynamodb", endpoint_url=DDB_ENDPOINT)
else:
    ddb = session.resource("dynamodb")

table = ddb.Table(TABLE_NAME)

# Schema:
# TopicMeta: PK=TOPIC#<subject>, SK=TOPIC#<topicId>, Type=TopicMeta, subject, title, estMinutes, GSI1PK=TOPIC_LIST, GSI1SK=<subject>#<sort>
# RevCard:   PK=CONTENT#<topicId>, SK=CARD#<cardId>, Type=RevCard, front, back, difficultyTag, GSI1PK=TOPIC#<topicId>, GSI1SK=CARD#<cardId>

def put_item(item: dict[str, Any]):
    table.put_item(Item=item)


def load_subject_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    subject = data["subject"]
    topics = data.get("topics", [])
    for idx, t in enumerate(topics):
        topic_id = t["id"]
        title = t.get("title", topic_id)
        est = int(t.get("estMinutes", 10))
        # TopicMeta
        put_item({
            "PK": f"TOPIC#{subject}",
            "SK": f"TOPIC#{topic_id}",
            "Type": "TopicMeta",
            "subject": subject,
            "title": title,
            "estMinutes": est,
            "GSI1PK": "TOPIC_LIST",
            "GSI1SK": f"{subject}#{idx:04d}",
        })
        # Cards
        for c in t.get("cards", []):
            put_item({
                "PK": f"CONTENT#{topic_id}",
                "SK": f"CARD#{c['id']}",
                "Type": "RevCard",
                "front": c.get("front", ""),
                "back": c.get("back", ""),
                "difficultyTag": c.get("tag"),
                "GSI1PK": f"TOPIC#{topic_id}",
                "GSI1SK": f"CARD#{c['id']}",
            })
        # Optional: MCQs retained as content items (could be used later)
        for q in t.get("mcq", []):
            put_item({
                "PK": f"CONTENT#{topic_id}",
                "SK": f"MCQ#{q['id']}",
                "Type": "MCQ",
                "stem": q.get("stem", ""),
                "choices": q.get("choices", []),
                "answer": int(q.get("answer", 0)),
                "explanation": q.get("explanation"),
                "GSI1PK": f"TOPIC#{topic_id}",
                "GSI1SK": f"MCQ#{q['id']}",
            })


def main():
    seed_dir = Path(__file__).parent
    files = list(seed_dir.glob("*.json"))
    if not files:
        print("No seed JSON files found.")
        return 0
    print(f"Seeding into table: {TABLE_NAME}")
    for p in files:
        print(f"- Loading {p.name}")
        load_subject_json(p)
    print("Done.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
