import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { HelpRungs, Rung, RungContent } from '@/components/views/HelpRungs';
import { classifyAnswer, logEvent, ClassifyAnswerRes, CommonErrorIn } from '@/lib/api';

// ── V2 schema types ────────────────────────────────────────────────────────

type CommonError = {
  category: string;
  pattern: string;
  wrong_answer_example: string;
  redirect_question: string;
};

type Step = {
  step_number: number;
  description: string;
  nudge: string;
  hint: string;
  worked_step: string;
  expected_answer: string;
  common_errors: CommonError[];
};

export type V2Problem = {
  normalised_form: string;
  full_solution: string;
  explain_it_back: string;
  steps: Step[];
  _schema_version: '2.0.0';
};

type Props = {
  problem: V2Problem;
  attemptId: string;
};

// ── Component ──────────────────────────────────────────────────────────────

type StepState = {
  revealed: Rung;                         // highest rung shown
  answerInput: string;
  diagnostic: ClassifyAnswerRes | null;   // last wrong-answer result
  correct: boolean;
  wrongCount: number;
};

function makeInitialStepStates(steps: Step[]): StepState[] {
  return steps.map(() => ({
    revealed: 1,
    answerInput: '',
    diagnostic: null,
    correct: false,
    wrongCount: 0,
  }));
}

export function HomeworkWorkspace({ problem, attemptId }: Props) {
  const [stepStates, setStepStates] = useState<StepState[]>(() =>
    makeInitialStepStates(problem.steps)
  );
  const [activeStep, setActiveStep] = useState(0);

  function updateStep(index: number, patch: Partial<StepState>) {
    setStepStates((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], ...patch };
      return next;
    });
  }

  async function handleReveal(stepIndex: number, rung: Rung) {
    updateStep(stepIndex, { revealed: rung });
    try {
      await logEvent({
        attempt_id: attemptId,
        event_type: 'rung_revealed',
        step_number: problem.steps[stepIndex].step_number,
        payload: { rung },
      });
    } catch { /* non-critical */ }
  }

  async function handleSubmitAnswer(stepIndex: number) {
    const step = problem.steps[stepIndex];
    const state = stepStates[stepIndex];
    if (!state.answerInput.trim()) return;

    try {
      const res = await classifyAnswer({
        attempt_id: attemptId,
        step_number: step.step_number,
        raw_input: state.answerInput,
        expected_answer: step.expected_answer,
        common_errors: step.common_errors as CommonErrorIn[],
      });

      if (res.is_correct) {
        updateStep(stepIndex, { correct: true, diagnostic: null });
        // Advance to next step automatically
        if (stepIndex + 1 < problem.steps.length) {
          setActiveStep(stepIndex + 1);
        }
      } else {
        updateStep(stepIndex, {
          diagnostic: res,
          wrongCount: state.wrongCount + 1,
          answerInput: '',
        });
      }
    } catch {
      // Fallback: treat as connection error, don't block the student
    }
  }

  const allDone = stepStates.every((s) => s.correct);

  return (
    <div className="space-y-6">
      {/* Problem statement */}
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-1">Question</p>
        <p className="text-base font-medium text-gray-900">{problem.normalised_form}</p>
      </div>

      {/* Step list */}
      {problem.steps.map((step, i) => {
        const state = stepStates[i];
        const isActive = i === activeStep;
        const isPast = state.correct;
        const isFuture = !isPast && !isActive;

        const rungContent: RungContent = {
          nudge: step.nudge,
          hint: step.hint,
          workedStep: step.worked_step,
          fullSolution: problem.full_solution,
        };

        return (
          <div
            key={step.step_number}
            className={`rounded-xl border p-5 transition-opacity ${
              isFuture ? 'opacity-40 pointer-events-none' : 'opacity-100'
            } ${isPast ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-white'}`}
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <span className="text-xs font-semibold uppercase tracking-wide text-gray-400">
                  Step {step.step_number}
                </span>
                <p className="mt-0.5 text-sm text-gray-800">{step.description}</p>
              </div>
              {isPast && (
                <span className="text-green-600 font-semibold text-sm ml-4">✓ Correct</span>
              )}
            </div>

            {!isPast && isActive && (
              <>
                {/* Rungs */}
                <HelpRungs
                  content={rungContent}
                  revealed={state.revealed}
                  onReveal={(rung) => handleReveal(i, rung)}
                />

                {/* Diagnostic panel (wrong answer feedback) */}
                {state.diagnostic && !state.diagnostic.is_correct && (
                  <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4">
                    <p className="text-sm font-semibold text-amber-800 mb-1">
                      {state.diagnostic.error_category === 'format'
                        ? 'Check your format'
                        : state.diagnostic.error_category === 'arithmetic'
                        ? 'Nearly there — check your arithmetic'
                        : 'Not quite'}
                    </p>
                    {state.diagnostic.redirect_question && (
                      <p className="text-sm text-amber-700">{state.diagnostic.redirect_question}</p>
                    )}
                    {/* After first wrong answer, offer shortcuts */}
                    {state.wrongCount >= 1 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-amber-300 text-amber-800 hover:bg-amber-100"
                          onClick={() =>
                            updateStep(i, {
                              revealed: Math.min(state.revealed + 1, 4) as Rung,
                              diagnostic: null,
                            })
                          }
                          disabled={state.revealed >= 4}
                        >
                          Show a smaller hint
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-amber-300 text-amber-800 hover:bg-amber-100"
                          onClick={() => handleReveal(i, 3)}
                          disabled={state.revealed >= 3}
                        >
                          Show me this step
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-gray-500"
                          onClick={() => updateStep(i, { diagnostic: null })}
                        >
                          Try again
                        </Button>
                      </div>
                    )}
                  </div>
                )}

                {/* Answer input */}
                <div className="mt-4 flex gap-2">
                  <Input
                    value={state.answerInput}
                    onChange={(e) => updateStep(i, { answerInput: e.target.value })}
                    onKeyDown={(e) => { if (e.key === 'Enter') handleSubmitAnswer(i); }}
                    placeholder="Your answer…"
                    className="flex-1"
                    aria-label={`Answer for step ${step.step_number}`}
                  />
                  <Button onClick={() => handleSubmitAnswer(i)}>Check</Button>
                </div>
              </>
            )}
          </div>
        );
      })}

      {/* All done */}
      {allDone && (
        <div className="rounded-lg border border-green-300 bg-green-50 p-5 text-center">
          <p className="text-lg font-semibold text-green-800">All steps complete!</p>
          <p className="mt-1 text-sm text-green-700">{problem.explain_it_back}</p>
        </div>
      )}
    </div>
  );
}
