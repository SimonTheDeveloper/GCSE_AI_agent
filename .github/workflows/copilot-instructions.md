# Copilot Instructions

This file guides GitHub Copilot when generating code for this
repository.

------------------------------------------------------------------------

## Development Workflow

Before implementing any change, Copilot should:

1.  Inspect the repository for existing implementations.
2.  Identify reusable components.
3.  Propose the **smallest pragmatic change**.
4.  Wait for approval before implementing.
5.  Implement only what is required for the current issue.

Avoid large refactors unless explicitly requested.

------------------------------------------------------------------------

## Product Overview

This repository implements an **AI-assisted GCSE tutoring system**.

Primary user flow:

1.  Student uploads or types a GCSE maths question.
2.  OCR extracts or cleans the text.
3.  Question is canonicalized and hashed.
4.  System checks whether the exercise already exists.
5.  If cached → return stored solution.
6.  If new → generate structured solution once and store it.
7.  Student receives hints, explanations, and answer checking.
8.  Progress is tracked for dashboards.

The system prioritizes:

-   low AI cost
-   deterministic pipelines
-   reuse of generated content

------------------------------------------------------------------------

## Core Principle

Every solved question becomes a reusable **Exercise** object.

Exercise objects are reused for:

-   hints
-   explanations
-   answer checking
-   analytics
-   curriculum tagging

Never regenerate a solution if it already exists.

------------------------------------------------------------------------

## Cost Control Rules

AI calls are the primary cost driver.

Always follow this order:

1.  cache lookup
2.  deterministic logic
3.  cheap model if needed
4.  expensive model as last resort

Avoid sending large prompts or conversation histories.

------------------------------------------------------------------------

## Prompt Strategy

Prompts should be:

-   short
-   deterministic
-   structured
-   validated

When generating new exercises, always request structured JSON output.

------------------------------------------------------------------------

## Follow‑Up Explanations

Follow-up prompts should include only:

-   cleaned question
-   relevant solution step
-   student follow-up text

Do not include full conversation history.

------------------------------------------------------------------------

## Answer Checking Strategy

Answer checking should use a layered approach:

1.  exact comparison
2.  normalized comparison
3.  rule-based validation
4.  LLM fallback only if ambiguous

LLMs must not be the primary grading mechanism.

------------------------------------------------------------------------

## Architecture Summary

Frontend - React + TypeScript

Backend - FastAPI (Python)

Database - DynamoDB

File storage - S3

Hosting - AWS Fargate

Payments - Stripe

Authentication - Cognito or lightweight alternative

All AI calls happen in the backend.

------------------------------------------------------------------------

## Code Quality Expectations

Prefer:

-   clear functions
-   typed models
-   small modules
-   explicit naming

Avoid:

-   unnecessary abstraction
-   deep inheritance hierarchies
-   premature complexity

The system should remain easy to debug.

------------------------------------------------------------------------

## When NOT to use AI

Do not add LLM calls for:

-   hint retrieval
-   progress summaries
-   dashboard calculations
-   usage analytics

These should be deterministic.

------------------------------------------------------------------------

## Development Reminder

When implementing features:

1.  inspect repository
2.  reuse existing components
3.  propose minimal solution
4.  wait for approval
5.  implement

Never introduce major architectural changes without approval.
