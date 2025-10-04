SHELL := /bin/bash

# Optional environment overrides
# export AWS_REGION=eu-west-1
# export DYNAMODB_TABLE_NAME=gcse_app
# export STACK_NAME=GcseAiStack

AWS_REGION ?=
DYNAMODB_TABLE_NAME ?=
STACK_NAME ?= GcseAiStack

.PHONY: help deploy destroy status seed frontend-build build-and-deploy outputs

help:
	@echo "Available targets:"
	@echo "  frontend-build       Build the React frontend (frontend/)"
	@echo "  deploy               Deploy CDK stack (infrastructure/cdk)"
	@echo "  build-and-deploy     Build frontend then deploy CDK stack"
	@echo "  status               Show CloudFormation + ECS status"
	@echo "  outputs              Show stack outputs (LB DNS, etc.)"
	@echo "  seed                 Load seed JSON into DynamoDB table"
	@echo "  destroy              Destroy CDK stack"

frontend-build:
	@echo "[frontend] install + build"
	@cd frontend && if [ -f package-lock.json ]; then npm ci; else npm install; fi && npm run build

outputs:
	@echo "[cdk] stack outputs ($(STACK_NAME))"
	@aws cloudformation describe-stacks --stack-name $(STACK_NAME) \
		--query 'Stacks[0].Outputs' --output table

status:
	@echo "[status] CloudFormation and ECS"
	@cd infrastructure/cdk && ./stack_status.sh $(STACK_NAME)

# Deploys the stack. Frontend files will be uploaded if frontend/build exists
# (s3deploy in the CDK stack).
deploy:
	@echo "[cdk] deploy $(STACK_NAME)"
	@cd infrastructure/cdk && cdk deploy --require-approval never

build-and-deploy: frontend-build deploy
	@echo "[done] build-and-deploy complete"

# Seeds DynamoDB using seed/*.json
seed:
	@echo "[seed] loading seed/*.json into DynamoDB"
	@export AWS_REGION=$${AWS_REGION:-$$(aws configure get region)}; \
	export DYNAMODB_TABLE_NAME=$${DYNAMODB_TABLE_NAME:-$(DYNAMODB_TABLE_NAME)}; \
	if [ -z "$$DYNAMODB_TABLE_NAME" ]; then export DYNAMODB_TABLE_NAME=gcse_app; fi; \
	python3 seed/load_seed.py

# Destroys the CDK stack
destroy:
	@echo "[cdk] destroy $(STACK_NAME)"
	@cd infrastructure/cdk && cdk destroy -f
