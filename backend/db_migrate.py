#!/usr/bin/env python3
"""
Add GSI2 to the DynamoDB table — run once before deploying Ticket 1.4.

GSI2 enables: get_latest_attempt_for_problem(problem_id, user_id)
  GSI2PK = "PROBLEM#{problem_id}#USER#{user_id}"
  GSI2SK = "ATTEMPT#{started_at_iso}"

Rollback: delete the GSI via the AWS console or re-run with --delete.

Usage:
    cd backend
    source .venv/bin/activate
    python db_migrate.py            # create GSI2 (idempotent)
    python db_migrate.py --delete   # remove GSI2
"""
import argparse
import os
import time

import boto3
from dotenv import load_dotenv

load_dotenv()

TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "gcse_app")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
ENDPOINT_URL = os.getenv("DYNAMODB_ENDPOINT_URL") or None
GSI2_NAME = os.getenv("DYNAMODB_GSI2", "GSI2")


def _client():
    return boto3.client("dynamodb", region_name=AWS_REGION, endpoint_url=ENDPOINT_URL)


def _existing_gsi_names(client) -> list[str]:
    desc = client.describe_table(TableName=TABLE_NAME)
    return [g["IndexName"] for g in desc["Table"].get("GlobalSecondaryIndexes", [])]


def _billing_mode(client) -> str:
    desc = client.describe_table(TableName=TABLE_NAME)
    return desc["Table"].get("BillingModeSummary", {}).get("BillingMode", "PROVISIONED")


def _wait_for_status(client, index_name: str, target: str) -> None:
    print(f"Waiting for {index_name} to reach {target}...")
    while True:
        desc = client.describe_table(TableName=TABLE_NAME)
        statuses = {
            g["IndexName"]: g["IndexStatus"]
            for g in desc["Table"].get("GlobalSecondaryIndexes", [])
        }
        current = statuses.get(index_name, "MISSING")
        print(f"  {index_name}: {current}")
        if current == target:
            break
        if target == "MISSING" and index_name not in statuses:
            break
        time.sleep(5)


def create(client) -> None:
    if GSI2_NAME in _existing_gsi_names(client):
        print(f"GSI '{GSI2_NAME}' already exists on '{TABLE_NAME}'. Nothing to do.")
        return

    gsi_spec: dict = {
        "IndexName": GSI2_NAME,
        "KeySchema": [
            {"AttributeName": "GSI2PK", "KeyType": "HASH"},
            {"AttributeName": "GSI2SK", "KeyType": "RANGE"},
        ],
        "Projection": {"ProjectionType": "ALL"},
    }
    if _billing_mode(client) == "PROVISIONED":
        gsi_spec["ProvisionedThroughput"] = {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}

    print(f"Creating GSI '{GSI2_NAME}' on table '{TABLE_NAME}'...")
    client.update_table(
        TableName=TABLE_NAME,
        AttributeDefinitions=[
            {"AttributeName": "GSI2PK", "AttributeType": "S"},
            {"AttributeName": "GSI2SK", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexUpdates=[{"Create": gsi_spec}],
    )
    _wait_for_status(client, GSI2_NAME, "ACTIVE")
    print(f"GSI '{GSI2_NAME}' is ACTIVE.")


def delete(client) -> None:
    if GSI2_NAME not in _existing_gsi_names(client):
        print(f"GSI '{GSI2_NAME}' does not exist on '{TABLE_NAME}'. Nothing to do.")
        return

    print(f"Deleting GSI '{GSI2_NAME}' from table '{TABLE_NAME}'...")
    client.update_table(
        TableName=TABLE_NAME,
        GlobalSecondaryIndexUpdates=[{"Delete": {"IndexName": GSI2_NAME}}],
    )
    _wait_for_status(client, GSI2_NAME, "MISSING")
    print(f"GSI '{GSI2_NAME}' deleted.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--delete", action="store_true", help="Remove GSI2 instead of creating it")
    args = parser.parse_args()

    c = _client()
    if args.delete:
        delete(c)
    else:
        create(c)
