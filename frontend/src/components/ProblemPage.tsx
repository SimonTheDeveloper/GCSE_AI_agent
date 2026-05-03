import { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { RawApiResponsePanel } from '@/components/views/HomeworkSubmissionView';
import {
  evaluateSubmission,
  getProblem,
  EvaluateRes,
  EvaluateMode,
  EvaluateTarget,
  FeedbackSegment,
  ProblemRes,
} from '@/lib/api';

// ── Types ──────────────────────────────────────────────────────────────────

// Three-way UI mode. Maps to (mode, target) pairs at evaluator-call time:
//   'free'    → mode=free,    target=main
//   'guided'  → mode=guided,  target=main
//   'simpler' → mode=guided,  target=simpler   (simpler-version is always
//               scaffolded — the whole point of it is gentler practice)
type UiMode = 'free' | 'guided' | 'simpler';

type SubmissionRecord = {
  submission: string;
  result: EvaluateRes;
  // The UI mode that was active when this submission was checked. Frozen
  // with the record so historical entries still render correctly even
  // after the student switches modes. Drives history filtering — simpler-
  // mode submissions are hidden when not in simpler mode, and vice versa.
  mode: UiMode;
};

type Props = {
  // Default UI mode on first arrival. Phase-2 default is "guided".
  defaultMode?: UiMode;
};

// ── Constants ──────────────────────────────────────────────────────────────

const FALLBACK_OPENING_PROMPT =
  'What would you try first? Type whatever comes to mind — partial working is fine.';
const FALLBACK_SIMPLER_OPENING_PROMPT =
  'Try this simpler version first — same idea, easier numbers.';

// ── Component ──────────────────────────────────────────────────────────────

export function ProblemPage({ defaultMode = 'guided' }: Props) {
  const { problemId } = useParams<{ problemId: string }>();
  const navigate = useNavigate();

  const [problem, setProblem] = useState<ProblemRes | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [mode, setMode] = useState<UiMode>(defaultMode);
  const [submission, setSubmission] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [history, setHistory] = useState<SubmissionRecord[]>([]);

  const attemptId = useMemo(() => crypto.randomUUID(), []);

  useEffect(() => {
    if (!problemId) {
      setLoadError('No problem id in URL.');
      return;
    }
    let cancelled = false;
    getProblem(problemId)
      .then((p) => { if (!cancelled) setProblem(p); })
      .catch((e) => { if (!cancelled) setLoadError(String(e?.message ?? e)); });
    return () => { cancelled = true; };
  }, [problemId]);

  async function handleSubmit() {
    if (!problemId || !submission.trim() || submitting) return;
    const text = submission;
    const submittedMode = mode;
    const evaluatorMode: EvaluateMode = submittedMode === 'free' ? 'free' : 'guided';
    const target: EvaluateTarget = submittedMode === 'simpler' ? 'simpler' : 'main';
    setSubmitting(true);
    try {
      const result = await evaluateSubmission({
        attempt_id: attemptId,
        problem_id: problemId,
        submission: text,
        mode: evaluatorMode,
        target,
      });
      setHistory((prev) => [...prev, { submission: text, result, mode: submittedMode }]);
      setSubmission('');
    } catch (e: any) {
      setHistory((prev) => [
        ...prev,
        {
          submission: text,
          mode: submittedMode,
          result: {
            is_correct: false,
            feedback_segments: [],
            prose_feedback: `Could not check your working: ${e?.message ?? e}`,
          },
        },
      ]);
    } finally {
      setSubmitting(false);
    }
  }

  if (loadError) {
    return (
      <div className="mx-auto max-w-3xl p-6">
        <p className="text-sm text-red-600">{loadError}</p>
        <Button variant="outline" className="mt-4" onClick={() => navigate('/homework')}>
          Back to homework
        </Button>
      </div>
    );
  }

  if (!problem) {
    return <div className="mx-auto max-w-3xl p-6 text-sm text-gray-500">Loading problem…</div>;
  }

  const simplerVersion = problem.ai_response?.simpler_version;
  const hasSimpler =
    simplerVersion &&
    typeof simplerVersion === 'object' &&
    typeof simplerVersion.question === 'string' &&
    simplerVersion.question.trim() &&
    typeof simplerVersion.solution === 'string' &&
    simplerVersion.solution.trim();

  // History bucketed by mode: simpler-mode submissions are shown only when
  // simpler mode is active; main submissions only when not. Keeps the
  // student's focus on what's in front of them.
  const visibleHistory = history.filter((r) =>
    mode === 'simpler' ? r.mode === 'simpler' : r.mode !== 'simpler',
  );

  // "Done" is per-track — completing the simpler version doesn't mark the
  // main problem complete, and vice versa.
  const allDoneInTrack = visibleHistory.some((r) => r.result.is_correct);

  // What's the question on the page right now?
  const displayedQuestion =
    mode === 'simpler' && hasSimpler
      ? (simplerVersion as any).question
      : problem.normalised_form;

  // Opening prompt for the active track, with track-specific fallback.
  const mainOpening =
    typeof problem.ai_response?.opening_prompt === 'string' && problem.ai_response.opening_prompt.trim()
      ? problem.ai_response.opening_prompt
      : FALLBACK_OPENING_PROMPT;
  const simplerOpening =
    hasSimpler && typeof (simplerVersion as any).opening_prompt === 'string' && (simplerVersion as any).opening_prompt.trim()
      ? (simplerVersion as any).opening_prompt
      : FALLBACK_SIMPLER_OPENING_PROMPT;
  const openingPrompt = mode === 'simpler' ? simplerOpening : mainOpening;

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      {/* Question */}
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
        <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-400">
          {mode === 'simpler' ? 'Simpler version' : 'Question'}
        </p>
        <p className="text-base font-medium text-gray-900">{displayedQuestion}</p>
      </div>

      {/* Mode toggle */}
      <ModeToggle mode={mode} onChange={setMode} simplerAvailable={Boolean(hasSimpler)} />

      {/* Submission history (filtered to current track) */}
      {visibleHistory.length > 0 && (
        <div className="space-y-4">
          {visibleHistory.map((record, i) => (
            <div key={i} className="space-y-3">
              <SubmissionFeedback record={record} />
              {/* Next prompt — only for the *last* visible guided/simpler
                  submission, since earlier ones are superseded by what the
                  student did next. */}
              {record.mode !== 'free'
                && i === visibleHistory.length - 1
                && record.result.next_prompt
                && !record.result.is_correct && (
                  <NextPromptBubble text={record.result.next_prompt} />
                )}
            </div>
          ))}
        </div>
      )}

      {/* Opening prompt — shown only on first arrival into the active track,
          and only when the active track is scaffolded (guided or simpler). */}
      {!allDoneInTrack && visibleHistory.length === 0 && mode !== 'free' && (
        <NextPromptBubble text={openingPrompt} />
      )}

      {/* Active input */}
      {!allDoneInTrack && (
        <div className="space-y-2">
          <Textarea
            value={submission}
            onChange={(e) => setSubmission(e.target.value)}
            placeholder="Show your working — type whatever you'd try."
            rows={6}
            className="font-mono text-sm"
            aria-label="Your working"
          />
          <div className="flex justify-end">
            <Button onClick={handleSubmit} disabled={submitting || !submission.trim()}>
              {submitting ? 'Checking…' : 'Check'}
            </Button>
          </div>
        </div>
      )}

      {/* Completion — track-aware. Simpler-version success offers a one-click
          return to the original problem; main-problem success shows the
          canonical solution. */}
      {allDoneInTrack && mode === 'simpler' && (
        <div className="rounded-lg border border-green-300 bg-green-50 p-5 text-center">
          <p className="text-lg font-semibold text-green-800">
            Nicely done with the simpler version.
          </p>
          <p className="mt-1 text-sm text-green-700">Ready to try the original problem?</p>
          <div className="mt-3">
            <Button onClick={() => setMode('guided')}>Try the original</Button>
          </div>
        </div>
      )}
      {allDoneInTrack && mode !== 'simpler' && (
        <div className="rounded-lg border border-green-300 bg-green-50 p-5 text-center">
          <p className="text-lg font-semibold text-green-800">Nicely done — you got it.</p>
          <p className="mt-1 text-sm text-green-700">
            {(problem.ai_response?.full_solution as string | undefined) ||
              'You reached the canonical answer.'}
          </p>
        </div>
      )}

      <div className="text-center">
        <button
          onClick={() => navigate('/homework')}
          className="text-sm text-gray-500 underline hover:text-gray-700"
        >
          Back to homework
        </button>
      </div>

      {/* Debug panel — shows the stored problem record including the full AI
          response. Mirrors the old workspace's debug panel so the same JSON
          is one click away during validation. */}
      <RawApiResponsePanel rawApiResponse={problem} />
    </div>
  );
}

// ── Mode toggle ────────────────────────────────────────────────────────────

function ModeToggle({
  mode,
  onChange,
  simplerAvailable,
}: {
  mode: UiMode;
  onChange: (next: UiMode) => void;
  simplerAvailable: boolean;
}) {
  return (
    <div className="flex gap-2">
      <ModeButton active={mode === 'guided'} onClick={() => onChange('guided')}>
        Guide me
      </ModeButton>
      <ModeButton active={mode === 'free'} onClick={() => onChange('free')}>
        Try yourself
      </ModeButton>
      <ModeButton
        active={mode === 'simpler'}
        disabled={!simplerAvailable}
        title={simplerAvailable ? undefined : 'Not available for this problem'}
        onClick={() => simplerAvailable && onChange('simpler')}
      >
        Simpler version
      </ModeButton>
    </div>
  );
}

function ModeButton({
  active,
  disabled,
  title,
  onClick,
  children,
}: {
  active: boolean;
  disabled?: boolean;
  title?: string;
  onClick: () => void;
  children: React.ReactNode;
}) {
  const base = 'rounded-md px-3 py-1.5 text-sm font-medium transition-colors';
  const cls = disabled
    ? `${base} cursor-not-allowed border border-gray-200 bg-gray-50 text-gray-400`
    : active
      ? `${base} border border-gray-900 bg-gray-900 text-white`
      : `${base} border border-gray-300 bg-white text-gray-700 hover:bg-gray-50`;
  return (
    <button type="button" disabled={disabled} title={title} onClick={onClick} className={cls}>
      {children}
    </button>
  );
}

// ── Next-prompt bubble ─────────────────────────────────────────────────────

function NextPromptBubble({ text }: { text: string }) {
  return (
    <div className="rounded-md border border-blue-200 bg-blue-50 px-4 py-3">
      <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-blue-500">
        Next move
      </p>
      <p className="text-sm text-blue-900">{text}</p>
    </div>
  );
}

// ── Markup rendering (same as Phase-1 FreeMode) ────────────────────────────

function SubmissionFeedback({ record }: { record: SubmissionRecord }) {
  const { submission, result } = record;

  if (result.is_correct) {
    return (
      <div className="rounded-md border border-green-200 bg-green-50 px-4 py-3">
        <p className="whitespace-pre-wrap font-mono text-sm text-gray-900">{submission}</p>
        <p className="mt-2 text-xs font-semibold text-green-700">✓ That's the answer.</p>
      </div>
    );
  }

  if (result.prose_feedback) {
    return (
      <div className="rounded-md border border-gray-200 bg-white p-4">
        <p className="whitespace-pre-wrap font-mono text-sm text-gray-900">{submission}</p>
        <p className="mt-3 border-t border-gray-100 pt-3 text-sm text-gray-700">
          {result.prose_feedback}
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-md border border-gray-200 bg-white p-4">
      <p className="mb-3 whitespace-pre-wrap font-mono text-sm leading-6">
        {result.feedback_segments.map((seg, i) => (
          <SegmentSpan key={i} seg={seg} />
        ))}
      </p>
      {result.feedback_segments.some((s) => s.comment) && (
        <ul className="space-y-1 border-t border-gray-100 pt-3 text-xs text-gray-700">
          {result.feedback_segments
            .map((seg, i) => ({ seg, i }))
            .filter(({ seg }) => seg.comment)
            .map(({ seg, i }) => (
              <li key={i} className="flex gap-2">
                <span className={`mt-0.5 inline-block h-2 w-2 shrink-0 rounded-full ${dotColour(seg.status)}`} />
                <span>{seg.comment}</span>
              </li>
            ))}
        </ul>
      )}
    </div>
  );
}

function SegmentSpan({ seg }: { seg: FeedbackSegment }) {
  if (!seg.text.trim()) return <span>{seg.text}</span>;
  return (
    <span className={segmentClass(seg.status)} title={seg.comment ?? undefined}>
      {seg.text}
    </span>
  );
}

function segmentClass(status: FeedbackSegment['status']): string {
  switch (status) {
    case 'correct':
      return 'bg-green-100 text-green-900 rounded px-0.5';
    case 'incomplete':
      return 'bg-amber-100 text-amber-900 rounded px-0.5';
    case 'wrong':
      return 'bg-red-100 text-red-900 rounded px-0.5';
    case 'unclear':
    default:
      return 'bg-gray-100 text-gray-700 rounded px-0.5';
  }
}

function dotColour(status: FeedbackSegment['status']): string {
  switch (status) {
    case 'correct':
      return 'bg-green-400';
    case 'incomplete':
      return 'bg-amber-400';
    case 'wrong':
      return 'bg-red-400';
    case 'unclear':
    default:
      return 'bg-gray-400';
  }
}
