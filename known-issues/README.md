# Known issues

This folder records open issues we've decided to defer rather than fix immediately. Each file is one issue. Files are deleted (or moved / marked resolved) when the issue is fixed.

The point is that next-time-us — or anyone else who picks up the work — should be able to read a single file and understand the symptom, what's been tried, and what to try next, without re-deriving any of it.

## File naming

`YYYY-MM-DD-short-description.md`

## Template

```markdown
# Title

**Date observed:** YYYY-MM-DD
**Status:** open | in-progress | resolved | won't-fix
**Severity:** blocker | high | medium | low
**Area:** evaluator | generator | frontend | infra | …

## Symptom

What the user sees. Be concrete.

## Reproduction

Steps. Specific inputs that trigger it. Environment notes (model, prompt version, anything else relevant).

## What we know

Hypothesis about cause. What we've ruled out. What we've tried that didn't work.

## Possible fixes

Options worth trying when we come back to this. Cheap-to-try first.

## Workaround

What to do in the meantime, if anything.
```
