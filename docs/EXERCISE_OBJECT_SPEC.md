# EXERCISE_OBJECT_SPEC.md

## Purpose

Defines the canonical structure of the **Exercise object**, the core
data unit of the tutoring system.

Every solved question becomes an Exercise object.

Exercise objects are reused for:

-   hints
-   explanations
-   answer checking
-   analytics
-   curriculum tagging

------------------------------------------------------------------------

# Design Principles

Exercise objects must be:

-   deterministic
-   reusable
-   immutable once stored
-   schema validated

------------------------------------------------------------------------

# Canonical Schema

Example structure:

{ "exercise_id": "uuid", "subject": "maths", "exam_board": "AQA",
"topic": "simultaneous_equations", "difficulty": "foundation",
"question_text_raw": "...", "question_text_clean": "...",
"final_answer": "...", "solution_steps": \[ "...", "..." \], "hint_1":
"...", "hint_2": "...", "hint_3": "...", "common_mistakes": \[ "..." \],
"curriculum_tags": \[ "algebra" \], "model_version": "...",
"created_at": "..." }

------------------------------------------------------------------------

# Field Descriptions

exercise_id\
Unique identifier.

subject\
Subject area (initially maths).

exam_board\
AQA, Edexcel, OCR, etc.

topic\
Curriculum topic classification.

difficulty\
Approximate GCSE difficulty level.

question_text_raw\
Original OCR or user text.

question_text_clean\
Normalized question text.

final_answer\
Expected final result.

solution_steps\
Step-by-step explanation.

hint_1 / hint_2 / hint_3\
Progressively stronger hints.

common_mistakes\
Typical errors students make.

curriculum_tags\
Additional classification metadata.

model_version\
AI model or prompt version used.

created_at\
Timestamp of creation.

------------------------------------------------------------------------

# Generation Requirements

When generating an Exercise object:

AI must return structured JSON matching the schema.

The response must be validated before storage.

------------------------------------------------------------------------

# Reuse Rules

Exercise objects should be reused whenever:

-   question hash matches existing exercise
-   minor formatting differences exist
-   OCR noise is present

Canonicalization should normalize questions before lookup.

------------------------------------------------------------------------

# Immutability

Exercise objects should not be modified after creation.

If improvements are needed:

Create a new version rather than editing the existing object.

------------------------------------------------------------------------

# Future Extensions

Possible additions:

-   multiple solution methods
-   diagram metadata
-   difficulty calibration
-   curriculum mapping for different exam boards
