# ARCHITECTURE.md

## Overview

The system is an AI‑assisted GCSE tutoring platform.

Student flow:

1.  upload or type question
2.  OCR extracts text
3.  question canonicalized
4.  cache lookup
5.  generate structured solution if not cached
6.  hints and explanations served
7.  progress tracked

Goals:

-   low AI cost
-   reusable solutions
-   simple architecture

------------------------------------------------------------------------

# System Components

Frontend - React + TypeScript

Backend - FastAPI (Python)

Database - DynamoDB

File storage - S3

Hosting - AWS Fargate

Payments - Stripe

Authentication - Cognito or simple email auth

------------------------------------------------------------------------

# Question Processing Pipeline

## Step 1: Input

Student provides image upload or typed question.

## Step 2: OCR

OCR extracts text and allows manual correction if needed.

## Step 3: Canonicalization

Normalize text and compute hash.

## Step 4: Cache Lookup

Return existing exercise if present.

## Step 5: Exercise Generation

LLM generates structured solution and hints.

------------------------------------------------------------------------

# Current Backend Structure

The backend is currently implemented as a **flat module** under `backend/`:

```
backend/
├─ main.py              # FastAPI app and all route handlers
├─ schemas.py           # Pydantic request/response models
├─ database.py / db.py  # DynamoDB access helpers
├─ auth.py              # Cognito token verification
├─ gcse_help_generator.py   # AI help orchestration
├─ gcse_help_prompts.py     # Prompt templates
├─ gcse_help_template.py    # Response templates
└─ scripts/
   └─ compare_maths_problems.py
```

The aspirational layered structure (`backend/app/api/`, `backend/app/services/`, etc.) described in [repository_map.md](repository_map.md) represents the **target architecture** as the codebase grows. Prefer extending the flat structure incrementally rather than reorganising everything at once.
