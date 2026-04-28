import { Button } from '@/components/ui/button';

export type Rung = 1 | 2 | 3 | 4;

export type RungContent = {
  nudge: string;      // Rung 1
  hint: string;       // Rung 2
  workedStep: string; // Rung 3
  fullSolution: string; // Rung 4
};

type Props = {
  content: RungContent;
  revealed: Rung; // highest rung currently visible (1 = only nudge shown)
  onReveal: (rung: Rung) => void;
};

const RUNG_LABELS: Record<Rung, string> = {
  1: 'Nudge',
  2: 'Hint',
  3: 'Worked step',
  4: 'Full solution',
};

const REVEAL_LABELS: Record<Rung, string> = {
  1: 'Show hint',
  2: 'Show worked step',
  3: 'Show full solution',
  4: '',
};

export function HelpRungs({ content, revealed, onReveal }: Props) {
  const rungs: Rung[] = [1, 2, 3, 4];

  const rungContent: Record<Rung, string> = {
    1: content.nudge,
    2: content.hint,
    3: content.workedStep,
    4: content.fullSolution,
  };

  return (
    <div className="space-y-3">
      {/* Progress dots */}
      <div className="flex items-center gap-1.5 mb-4" aria-label="Help level indicator">
        {rungs.map((r) => (
          <div
            key={r}
            className={`h-2 w-2 rounded-full transition-colors ${
              r <= revealed ? 'bg-amber-500' : 'bg-gray-200'
            }`}
          />
        ))}
        <span className="ml-2 text-xs text-gray-500">{RUNG_LABELS[revealed]}</span>
      </div>

      {/* Rung cards */}
      {rungs.map((r) => {
        if (r > revealed) {
          if (r === revealed + 1) {
            // Show the "unlock" button for the next rung
            return (
              <div key={r} className="rounded-lg border border-dashed border-gray-300 p-4 text-center">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onReveal(r as Rung)}
                  className="text-amber-700 border-amber-300 hover:bg-amber-50"
                >
                  {REVEAL_LABELS[revealed as Rung]} ↓
                </Button>
              </div>
            );
          }
          // Remaining locked rungs — not rendered at all (security: no DOM leakage)
          return null;
        }

        // r <= revealed: show the content
        return (
          <div
            key={r}
            className={`rounded-lg border p-4 ${
              r === 1 ? 'border-blue-200 bg-blue-50' :
              r === 2 ? 'border-amber-200 bg-amber-50' :
              r === 3 ? 'border-orange-200 bg-orange-50' :
              'border-red-200 bg-red-50'
            }`}
          >
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1">
              {RUNG_LABELS[r]}
            </p>
            <p className="text-sm text-gray-800 whitespace-pre-wrap">{rungContent[r]}</p>
          </div>
        );
      })}
    </div>
  );
}
