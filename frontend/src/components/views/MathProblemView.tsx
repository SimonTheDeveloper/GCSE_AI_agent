import { Card } from "../ui/card";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Alert } from "../ui/alert";
import { Progress } from "../ui/progress";
import { CheckCircle2, XCircle, ChevronRight } from 'lucide-react';

interface ProblemStep {
  stepNumber: number;
  prompt: string;
  expectedAnswer: string;
  hint: string;
}

export interface MathProblemViewProps {
  problem: {
    id: number;
    title: string;
    question: string;
    steps: ProblemStep[];
  };
  currentStepIndex: number;
  stepAnswers: string[];
  stepFeedback: ('correct' | 'incorrect' | null)[];
  showHint: boolean;
  attempts: number;
  progress: number;
  completedSteps: number;
  allStepsComplete: boolean;
  onStepAnswerChange: (value: string) => void;
  onCheckAnswer: () => void;
  onGoToStep: (index: number) => void;
  onToggleHint: () => void;
  onReset: () => void;
  onKeyDown?: (e: React.KeyboardEvent) => void;
}

export function MathProblemView({
  problem,
  currentStepIndex,
  stepAnswers,
  stepFeedback,
  showHint,
  attempts,
  progress,
  completedSteps,
  allStepsComplete,
  onStepAnswerChange,
  onCheckAnswer,
  onGoToStep,
  onToggleHint,
  onReset,
  onKeyDown
}: MathProblemViewProps) {
  const currentStep = problem.steps[currentStepIndex];

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="space-y-6">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2>{problem.title}</h2>
              <div className="text-sm text-gray-600">
                Step {currentStepIndex + 1} of {problem.steps.length}
              </div>
            </div>
            
            <div className="mb-4">
              <Progress value={progress} className="h-2" />
              <p className="text-sm text-gray-600 mt-2">
                {completedSteps} of {problem.steps.length} steps completed
              </p>
            </div>

            <div className="p-6 bg-blue-50 rounded-lg border border-blue-200">
              <h4 className="text-blue-900 mb-2">Problem</h4>
              <p className="whitespace-pre-line text-gray-700">{problem.question}</p>
            </div>
          </div>

          {/* Step Progress Indicators */}
          <div className="flex gap-2 flex-wrap">
            {problem.steps.map((step, index) => (
              <button
                key={index}
                onClick={() => onGoToStep(index)}
                className={`px-4 py-2 rounded-lg transition-all ${
                  index === currentStepIndex
                    ? 'bg-blue-600 text-white'
                    : stepFeedback[index] === 'correct'
                    ? 'bg-green-100 text-green-800 border border-green-300'
                    : index < currentStepIndex
                    ? 'bg-gray-100 text-gray-600 cursor-pointer hover:bg-gray-200'
                    : 'bg-gray-50 text-gray-400 cursor-not-allowed'
                }`}
                disabled={index > currentStepIndex && stepFeedback[index - 1] !== 'correct'}
              >
                {stepFeedback[index] === 'correct' ? (
                  <span className="flex items-center gap-1">
                    <CheckCircle2 className="h-4 w-4" />
                    Step {index + 1}
                  </span>
                ) : (
                  `Step ${index + 1}`
                )}
              </button>
            ))}
          </div>

          {/* Current Step */}
          <Card className="p-5 bg-gray-50 border-2 border-blue-300">
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center">
                  {currentStepIndex + 1}
                </div>
                <div className="flex-1">
                  <h4 className="mb-2">Step {currentStepIndex + 1}</h4>
                  <p className="text-gray-700">{currentStep.prompt}</p>
                </div>
              </div>

              <div className="space-y-3 ml-11">
                <div className="flex gap-3">
                  <Input
                    id="step-answer"
                    type="text"
                    value={stepAnswers[currentStepIndex]}
                    onChange={(e) => onStepAnswerChange(e.target.value)}
                    onKeyDown={onKeyDown}
                    placeholder="Type your answer here..."
                    className="flex-1 bg-white"
                    disabled={stepFeedback[currentStepIndex] === 'correct'}
                  />
                  <Button 
                    onClick={onCheckAnswer} 
                    disabled={!stepAnswers[currentStepIndex].trim() || stepFeedback[currentStepIndex] === 'correct'}
                  >
                    {currentStepIndex === problem.steps.length - 1 ? 'Finish' : 'Next Step'}
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </div>

                {stepFeedback[currentStepIndex] === 'incorrect' && (
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={onToggleHint}
                  >
                    {showHint ? 'Hide Hint' : 'Show Hint'}
                  </Button>
                )}

                {showHint && stepFeedback[currentStepIndex] === 'incorrect' && (
                  <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <p className="text-sm text-yellow-800">💡 {currentStep.hint}</p>
                  </div>
                )}
              </div>

              {stepFeedback[currentStepIndex] && (
                <Alert className={stepFeedback[currentStepIndex] === 'correct' ? 'bg-green-50 border-green-200 ml-11' : 'bg-red-50 border-red-200 ml-11'}>
                  <div className="flex items-center gap-2">
                    {stepFeedback[currentStepIndex] === 'correct' ? (
                      <>
                        <CheckCircle2 className="h-5 w-5 text-green-600" />
                        <div>
                          <h4 className="text-green-800">Correct!</h4>
                          <p className="text-green-700">
                            {currentStepIndex === problem.steps.length - 1 
                              ? 'You completed the problem!' 
                              : 'Moving to the next step...'}
                          </p>
                        </div>
                      </>
                    ) : (
                      <>
                        <XCircle className="h-5 w-5 text-red-600" />
                        <div>
                          <h4 className="text-red-800">Not quite right</h4>
                          <p className="text-red-700">Try again or view a hint.</p>
                        </div>
                      </>
                    )}
                  </div>
                </Alert>
              )}
            </div>
          </Card>

          {/* Completed Steps Summary */}
          {completedSteps > 0 && !allStepsComplete && (
            <div className="space-y-2">
              <h4 className="text-gray-700">Completed Steps:</h4>
              <div className="space-y-2">
                {problem.steps.map((step, index) => (
                  stepFeedback[index] === 'correct' && index < currentStepIndex && (
                    <div key={index} className="p-3 bg-green-50 border border-green-200 rounded-lg flex items-start gap-2">
                      <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                      <div className="flex-1">
                        <p className="text-sm text-gray-700">{step.prompt}</p>
                        <p className="text-green-700 font-mono">→ {stepAnswers[index]}</p>
                      </div>
                    </div>
                  )
                ))}
              </div>
            </div>
          )}

          {allStepsComplete && (
            <div className="space-y-4">
              <Alert className="bg-green-50 border-green-200">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-6 w-6 text-green-600" />
                  <div>
                    <h4 className="text-green-800">Problem Completed! 🎉</h4>
                    <p className="text-green-700">Excellent work! You solved all steps correctly.</p>
                  </div>
                </div>
              </Alert>
              <Button onClick={onReset} variant="outline">
                Try Again
              </Button>
            </div>
          )}

          <div className="pt-2 text-sm text-gray-600 border-t">
            Total attempts: {attempts}
          </div>
        </div>
      </Card>
    </div>
  );
}
