# CONTRIBUTING_AI.md

## Purpose

This document defines rules for contributors and AI coding assistants
when modifying AI-related functionality.

Goals: - keep AI usage predictable - control cost - keep architecture
simple - ensure consistent outputs

------------------------------------------------------------------------

# AI Usage Philosophy

AI should be used **only where deterministic logic is insufficient**.

Preferred order of solutions:

1.  cached result
2.  deterministic logic
3.  rule-based logic
4.  small AI call
5.  large reasoning AI call (last resort)

AI must never be the default option.

------------------------------------------------------------------------

# Prompt Design Rules

Prompts should:

-   be short
-   produce structured outputs
-   avoid unnecessary context
-   avoid sending full conversation history

Always request **structured JSON responses** where possible.

------------------------------------------------------------------------

# Prompt Location

Prompt templates must live in:

backend/app/prompts/

Never scatter prompt strings throughout the codebase.

Each prompt should have:

-   clear name
-   version comment
-   associated schema

------------------------------------------------------------------------

# Cost Control

Before adding a new AI call ask:

1.  Can the answer be retrieved from cache?
2.  Can deterministic logic solve it?
3.  Can a rule-based system solve it?

Only then consider AI.

------------------------------------------------------------------------

# AI Output Validation

All AI outputs must be validated using typed schemas (Pydantic).

Invalid responses should trigger:

1.  retry with repair prompt
2.  fallback response

Never store unvalidated AI output.

------------------------------------------------------------------------

# Approved AI Use Cases

AI may be used for:

-   exercise generation
-   follow-up explanation
-   ambiguous answer checking
-   curriculum tagging (offline)

AI should not be used for:

-   hints (pre-generated)
-   dashboards
-   analytics
-   usage summaries

------------------------------------------------------------------------

# Development Workflow

When implementing AI features:

1.  inspect existing prompts
2.  reuse schemas
3.  update prompt file
4.  update service logic
5.  add validation
6.  add tests

------------------------------------------------------------------------

# Logging

AI interactions should log:

-   prompt type
-   model used
-   token usage estimate
-   success/failure

Logs must not contain student personal data.
