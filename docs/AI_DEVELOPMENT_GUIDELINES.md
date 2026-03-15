# AI_DEVELOPMENT_GUIDELINES.md

## Purpose

Guidelines for AI‑assisted development (GitHub Copilot, agents).

Workflow: 1. Inspect the repository first. 2. Reuse existing patterns
when possible. 3. Propose the smallest pragmatic change. 4. Wait for
approval before implementing.

Avoid large refactors unless explicitly requested.

------------------------------------------------------------------------

# Product Overview

This repository implements an **AI-assisted GCSE tutoring system**
focused initially on **GCSE Maths**.

Students can: - upload or type a question - receive step‑by‑step
explanations - request hints - ask follow‑up questions - submit
answers - track progress

Design priorities: - low cost - deterministic pipelines - reusable
exercise objects

------------------------------------------------------------------------

# Core Architectural Principle

Every solved question becomes an **Exercise object**.

Exercise objects are reused for: - hints - explanations - answer
checking - analytics - curriculum tagging

Avoid regenerating solutions whenever possible.

------------------------------------------------------------------------

# Cost Control Rules

AI calls are the main cost driver.

Always: 1. cache lookup first 2. deterministic logic second 3. cheap
model third 4. expensive model last

Never call an LLM if the result can be derived from stored data.

------------------------------------------------------------------------

# Follow‑Up Explanations

Send only: - cleaned question - relevant solution step - student
follow‑up

Never send the full conversation history.

------------------------------------------------------------------------

# Answer Checking Strategy

Layered approach:

1.  exact comparison
2.  normalized comparison
3.  rule‑based validation
4.  LLM fallback only if ambiguous

LLMs should **not** be the primary grading method.

------------------------------------------------------------------------

# Copilot Development Workflow

Before writing code:

1.  search repository for similar code
2.  reuse existing utilities
3.  propose smallest solution
4.  wait for approval

After approval: - implement minimal code - add tests where appropriate
