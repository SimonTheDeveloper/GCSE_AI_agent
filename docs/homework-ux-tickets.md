# Homework UX — implementation tickets

Three milestones, ordered by dependency. Each ticket is sized for one focused Claude Code session. Acceptance criteria are written so a reviewer can verify the work without ambiguity. Where a design decision has already been made in conversation, it's stated explicitly so Claude Code doesn't reinvent it.

---

## Milestone 1 — Fix the leak, then build the ladder

The current UI shows the full worked solution next to the input box. Until that's fixed, none of the pedagogy works. This milestone is about gating help correctly and capturing the data that lets us teach better.

---

### Ticket 1.1 — Hide worked solution behind progressive reveal

**Why:** A motivated student reads the worked solution; a tired student copies it. The whole "learn by doing" premise depends on the answer not being visible while the student is supposed to be solving.

**Scope:**
- Replace the always-visible Nudge / Worked / Overall Hint stack on the right-hand panel with a four-rung ladder where only Rung 1 (Nudge) is visible by default. Rungs 2–4 are visible as locked cards with a one-line description of what they contain, but their content is hidden.
- Rungs, in order:
  1. Nudge — conceptual question, never gives the operation
  2. Hint — names the operation but not the numbers
  3. Worked step — arithmetic for the current step only, not the full solution
  4. Full solution — the entire problem worked out
- Each locked rung has a button to reveal it. Revealing a rung does not auto-reveal subsequent rungs.
- A "Help used" progress indicator sits at the top of the panel: four dots, filled as rungs are revealed.
- The button on Rung 1 reads "Smaller hint ↓" not "Show more" — the framing is that each click gives less help, not more.

**Acceptance:**
- On a fresh problem load, only the Nudge content is visible. Rungs 2, 3, 4 show as locked cards with their one-line descriptions.
- Clicking a rung reveals only that rung's content.
- The progress indicator updates in real time.
- An automated test verifies that Rung 4 content (full solution) is not present in the DOM until the user has clicked to reveal it. This is non-negotiable — if the content is hidden via CSS only, copy-paste leaks it.

**Out of scope:** the diagnostic state for wrong answers (Ticket 1.3), the explain-it-back prompt (Ticket 2.1).

**Design reference:** the panel mockup discussed in chat. Use the existing colour palette already in the app.

---

### Ticket 1.2 — Backend: generate the four rungs at problem-ingestion time

**Why:** The AI call that currently generates the explanation needs to produce structured output for all four rungs, plus the per-step diagnostic context Ticket 1.3 will need. Generating these on demand per click is too slow and too expensive.

**Scope:**
- Update the AI prompt that runs on problem submission to return a structured object per step:
  ```
  {
    step_number: int,
    nudge: string,            // conceptual question, no operation named
    hint: string,             // names the operation, not the numbers
    worked_step: string,      // arithmetic for this step only
    expected_answer: string,  // the canonical answer for this step
    common_errors: [          // for Ticket 1.3
      { category: "conceptual" | "procedural" | "arithmetic" | "format",
        pattern: string,      // e.g. "added 5 instead of subtracting"
        wrong_answer_example: string,
        redirect_question: string }
    ]
  }
  ```
- Plus one top-level `full_solution` string for Rung 4.
- Persist the full structured response with the problem record. The frontend reads from the persisted record, not from a fresh AI call per rung click.

**Acceptance:**
- A new problem submission produces and persists the full structured response in one AI call.
- The frontend can render any rung from the persisted data without hitting the AI again.
- The `common_errors` array contains at least 2 entries per step for typical problems (the AI prompt must be tuned to actually generate these — see test fixture below).
- Test fixture: `2x + 5 = 17` produces `common_errors` for step 1 that includes at least the "added instead of subtracted" pattern.

**Note:** The new ingestion prompt (v2) is already in DynamoDB as a draft. It can be activated via the admin UI at `/admin/prompts` once the frontend is ready for the new schema.

---

### Ticket 1.3 — Wrong-answer diagnostic state

**Why:** Right now wrong answers are wasted — the most valuable signal in the whole session is "what did the student actually do?" and we throw it away with a binary correct/incorrect.

**Scope:**
- When a student submits an answer that doesn't match `expected_answer` for the current step, classify the error and show the diagnostic panel instead of a generic "wrong" message.
- Classification logic, in order:
  1. If the input doesn't parse as a maths expression — format error. Show "I'm not sure how to read that" with parsing suggestions.
  2. If it matches a `common_errors` pattern from the persisted data — show the corresponding redirect_question, plus a side-by-side mirror of what they did vs what cancels the operation.
  3. If it's a number that's close to the expected answer (within an arithmetic-slip distance) — arithmetic slip. Gentle tone: "Your method is right, check the arithmetic."
  4. Otherwise — fallback diagnostic: "That doesn't match — let's check your working" plus the Nudge from Rung 1 if not already shown.
- Tone: amber, not red. "Not quite — let's look at what happened" not "Wrong" or "Incorrect".
- After one wrong answer, surface "Smaller hint" and "Show me this step" as exit-ramp buttons alongside "Try again."

**Acceptance:**
- Submitting `2x = 22` for step 1 of `2x + 5 = 17` triggers the conceptual diagnostic with the correct mirror.
- Submitting `2x = 13` triggers the arithmetic-slip path, not the conceptual one.
- Submitting `banana` triggers the format-error path.
- Visual styling uses amber semantic colours, not red.
- Each wrong answer logs `{step, attempt_number, error_category, raw_input}` to the attempts table (Ticket 1.4).

**Implementation note:** Push error classification to the backend. The frontend sends raw input + expected answer; the backend classifies it deterministically (no AI for format/arithmetic-slip, the `classify` prompt in DynamoDB for unmatched patterns).

---

### Ticket 1.4 — Data model: problems, attempts, step_events

**Why:** Without this, none of Layer 2+ pedagogy is possible. Should land before or alongside Ticket 1.3, because 1.3 needs somewhere to write event logs.

**Scope:**

Three tables:

`problems`
- id, user_id, created_at
- raw_input (text, with optional image URL)
- normalised_form (text)
- topic_tags (string array — e.g. `["linear_equations", "two_step", "integer_coefficients"]`)
- difficulty (int 1–5, AI-generated)
- ai_response (jsonb — the full structured response from Ticket 1.2)

`attempts`
- id, problem_id, user_id, started_at, completed_at
- outcome (enum: `solved_unaided`, `solved_with_hints`, `revealed_full_solution`, `abandoned`)
- max_rung_revealed (0–4)
- active_time_seconds (int — pause when tab unfocused)
- explanation_text (text, nullable — for Milestone 2)
- explanation_rubric (jsonb, nullable)

`step_events`
- id, attempt_id, step_number, event_type, created_at
- event_type enum: `attempt_submitted`, `rung_revealed`, `step_completed`, `hint_dismissed_before_answer`
- payload (jsonb — depends on event_type, e.g. `{error_category, raw_input}` for attempts)

**Acceptance:**
- Migrations land cleanly, with rollback.
- Tag generation runs at problem-ingestion time. The AI prompt produces 3–6 tags per problem from a controlled vocabulary (start with ~30 tags covering GCSE algebra; expand later).
- Every rung reveal, every wrong answer, every step completion writes a `step_events` row.
- A simple admin query can return: "for user X, all attempts in the last 7 days with outcome and max_rung_revealed."

**Note on DynamoDB:** The three logical "tables" need to be designed as DynamoDB access patterns before writing migrations. Key design question: "all attempts for user X in last 7 days" and "all step_events for attempt Y" both need careful PK/SK choices and likely a GSI. Sketch access patterns first.

**Explicitly not yet:** spaced-repetition state, per-tag mastery scores. Those are derived in Milestone 3.

---

## Milestone 2 — The metacognitive layer

Once the ladder works and we're capturing struggle data, add the prompt that turns "got the answer" into "understood the answer."

---

### Ticket 2.1 — Explain-it-back prompt after correct final answer

**Why:** Articulating *why* a method works roughly doubles long-term retention vs. just solving. Without this prompt, the system teaches procedure, not understanding.

**Scope:**
- After the student submits a correct answer to the final step of a problem, before marking the problem complete, show the explain-it-back panel.
- The panel contains:
  - A success banner ("x = 6 is correct") with a one-line summary of attempts and hints used.
  - A single targeted question — generated by the AI at problem-ingestion time and stored on the problem record. The question must probe the *conceptual decision point*, not recite the procedure.
  - A textarea for free-text response, with placeholder "Type your reasoning..."
  - 2–3 sentence-starter chips below the textarea, AI-generated, each pointing at a different angle on the same concept.
  - A primary "Submit explanation" button and a secondary "Skip" button.
  - Footer copy explaining why this matters (retention claim).
- On submit, the AI scores the explanation against a 3-boolean rubric specific to the problem (also generated at ingestion time and stored). Possible outcomes:
  - Solid (2–3 booleans true) — mark complete, optionally surface similar-problem suggestion.
  - Partial (1 boolean true) — one targeted follow-up question, then mark complete regardless of response.
  - Empty / wrong — show canonical explanation framed as "Here's one way to think about it," mark concept as `partially_understood` in attempt record. Do not punish.

**Skip rules:**
- Don't fire the prompt at all if the attempt was `solved_unaided` on first try AND on a problem of difficulty ≤ 2. Mastery already demonstrated, prompt feels patronising.
- Always fire if any hint was revealed or any wrong answer was submitted.
- Add a user preference toggle "Always ask me to explain my answers" in settings, default on.

**Acceptance:**
- The prompt fires at the right moments per the skip rules.
- Generated questions probe concepts, not procedures (verify on 5 sample problems in the test fixture).
- Sentence-starter chips, when clicked, populate the textarea with the starter text and place the cursor at the end.
- Submit writes `explanation_text` and `explanation_rubric` to the attempts table.
- Skip writes `explanation_text = null` and a `skipped: true` flag, and is logged separately for analytics.

---

### Ticket 2.2 — Self-recovery tracking

**Why:** A student who reveals a hint and then dismisses it before answering has just demonstrated learning in real time. This is the single strongest signal in the whole system.

**Scope:**
- Add an "I figured it out" button at the top of the help panel whenever any rung above 0 is revealed.
- Clicking it collapses the revealed rungs back to locked state and logs a `hint_dismissed_before_answer` event with the rung level that was dismissed.
- If the student then submits the correct answer, the attempt outcome is `solved_with_hints` but the attempt record is flagged `self_recovered: true`.

**Acceptance:**
- Button appears only when at least one rung is revealed, and disappears when all rungs are dismissed.
- Dismissal logs the event correctly.
- A self-recovered correct submission is correctly flagged in the attempts table.

---

## Milestone 3 — The Review tab

Once Milestones 1 and 2 are running for a few weeks of real data, build the surfaces that make the longitudinal data useful.

---

### Ticket 3.1 — Per-tag mastery scoring

**Scope:**
- Mastery score per `(user_id, topic_tag)` pair, computed from attempts on problems with that tag.
- Score is a weighted average:
  - `solved_unaided` on first try = +1.0
  - `self_recovered` = +0.8
  - `solved_with_hints` = +0.4 to +0.7 depending on max_rung_revealed
  - `revealed_full_solution` = 0
  - `abandoned` = -0.2
- Exponential time decay, half-life ~14 days (configurable).
- Recompute after every attempt.

---

### Ticket 3.2 — Similar-problem suggestion after solve

**Scope:**
- After a problem is marked complete, generate one similar problem matching the same primary topic tag(s) but with different numbers.
- Surface as a "Try this on your own" card.
- If the student solves the similar problem `solved_unaided` on first try, flag the original concept as `mastered`.
- The `similar` prompt is already in DynamoDB and ready to use.

---

### Ticket 3.3 — Review tab UI

**Scope (v1):**
- Topic mastery overview: list of topics with mastery score visualised as a horizontal bar, sorted by lowest mastery first.
- Recent activity: last 10 problems with outcome, time, hints used.
- Error patterns: top 3 most frequent error categories from the last 30 days.
- Suggested practice: 3 problems from spaced repetition (topic where last attempt was 5+ days ago AND mastery score below 0.7).

---

## Suggested execution order

1.4 (data model) → 1.2 (structured AI response) → 1.1 (rung UI) → 1.3 (diagnostic) → 2.1 (explain-it-back) → 2.2 (self-recovery) → wait for data → 3.1 → 3.2 → 3.3

Tickets 1.4 and 1.2 can happen in parallel if you have backend capacity. Everything in Milestone 3 should wait until you have at least a few hundred real attempts in the database.
