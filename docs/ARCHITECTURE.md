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
