# GCSE AI Tutor

An AI-assisted GCSE tutoring application, initially focused on GCSE Maths.

Students submit questions by image or text. The backend extracts, normalises, and solves the question, building a reusable **Exercise object** that powers hints, step-by-step explanations, answer checking, and progress tracking.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript (Vite) |
| Backend | FastAPI (Python) |
| Database | DynamoDB (single-table design) |
| File storage | S3 |
| Hosting | AWS Fargate |
| Auth | Amazon Cognito |
| AI | OpenAI (configurable model) |
| OCR | Tesseract (optional) |
| Infrastructure | AWS CDK |

---

## Local Development

### Backend

```sh
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # or: pip install fastapi uvicorn python-dotenv boto3 openai pillow pytesseract
```

Create `backend/.env`:
```env
DYNAMODB_TABLE_NAME=gcse_app
AWS_REGION=eu-west-2
OPENAI_API_KEY=sk-...           # optional – enables AI help
OPENAI_MODEL=gpt-4o-mini        # optional – defaults to gpt-3.5-turbo
```

Run:
```sh
cd backend
uvicorn main:app --reload --port 8000
```

### Frontend

```sh
cd frontend
npm install
npm run dev
```

The React app runs on `http://localhost:5173` by default, proxying API calls to `http://localhost:8000`.

### OCR (optional)

Install Tesseract to enable image text extraction:
```sh
brew install tesseract          # macOS
# apt install tesseract-ocr     # Debian/Ubuntu
```

Then install the Python bindings:
```sh
pip install pytesseract Pillow
```

---

## AWS Deployment

### Prerequisites

- Python 3.9+
- Node.js 18+
- AWS CDK CLI: `npm install -g aws-cdk`
- AWS CLI configured: `aws configure`

### Deploy

```sh
# Bootstrap CDK (first time only)
cdk bootstrap aws://ACCOUNT-NUMBER/REGION

# Build frontend
cd frontend && npm install && npm run build && cd ..

# Deploy all stacks
cdk deploy
```

---

## GitHub Actions

The CI workflow uses OIDC to assume an IAM role for deployments.
Replace the placeholders in `.github/workflows/` with your AWS account ID and region.

### Required IAM role trust relationship

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:sub": "repo:SimonTheDeveloper/GCSE_AI_agent:ref:refs/heads/main",
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
```

Attach `AmazonEC2ContainerRegistryPowerUser` and a custom CDK deploy policy (see [AWS docs](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html)).

---

## Key docs

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system design and data flow
- [docs/EXERCISE_OBJECT_SPEC.md](docs/EXERCISE_OBJECT_SPEC.md) — core data model
- [docs/repository_map.md](docs/repository_map.md) — where code should live
- [docs/AGENT_CONTEXT.md](docs/AGENT_CONTEXT.md) — guide for AI coding agents
