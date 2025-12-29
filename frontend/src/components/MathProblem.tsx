import { useState, useEffect } from 'react';
import { MathProblemView } from './views/MathProblemView';

interface ProblemStep {
  stepNumber: number;
  prompt: string;
  expectedAnswer: string;
  hint: string;
}

interface MathProblemProps {
  problem: {
    id: number;
    title: string;
    question: string;
    steps: ProblemStep[];
  };
  onSolved: (problemId: number) => void;
  currentStepIndex: number;
  onStepChange: (stepIndex: number) => void;
}

export function MathProblem({ problem, onSolved, currentStepIndex, onStepChange }: MathProblemProps) {
  const [stepAnswers, setStepAnswers] = useState<string[]>(new Array(problem.steps.length).fill(''));
  const [stepFeedback, setStepFeedback] = useState<('correct' | 'incorrect' | null)[]>(
    new Array(problem.steps.length).fill(null)
  );
  const [showHint, setShowHint] = useState(false);
  const [attempts, setAttempts] = useState(0);

  const currentStep = problem.steps[currentStepIndex];
  const completedSteps = stepFeedback.filter(f => f === 'correct').length;
  const progress = (completedSteps / problem.steps.length) * 100;

  useEffect(() => {
    // Reset when problem changes
    setStepAnswers(new Array(problem.steps.length).fill(''));
    setStepFeedback(new Array(problem.steps.length).fill(null));
    setShowHint(false);
    setAttempts(0);
    onStepChange(0);
  }, [problem.id]);

  const checkStepAnswer = () => {
    const userAnswer = stepAnswers[currentStepIndex].trim().toLowerCase();
    const expectedAnswer = currentStep.expectedAnswer.toLowerCase();
    const isCorrect = userAnswer === expectedAnswer;
    
    const newFeedback = [...stepFeedback];
    newFeedback[currentStepIndex] = isCorrect ? 'correct' : 'incorrect';
    setStepFeedback(newFeedback);
    setAttempts(attempts + 1);

    if (isCorrect) {
      setShowHint(false);
      // Move to next step after a brief delay
      if (currentStepIndex < problem.steps.length - 1) {
        setTimeout(() => {
          onStepChange(currentStepIndex + 1);
        }, 800);
      } else {
        // All steps completed
        onSolved(problem.id);
      }
    }
  };

  const updateStepAnswer = (value: string) => {
    const newAnswers = [...stepAnswers];
    newAnswers[currentStepIndex] = value;
    setStepAnswers(newAnswers);
    
    // Clear feedback when user changes answer
    if (stepFeedback[currentStepIndex] === 'incorrect') {
      const newFeedback = [...stepFeedback];
      newFeedback[currentStepIndex] = null;
      setStepFeedback(newFeedback);
    }
  };

  const goToStep = (index: number) => {
    // Can only go to completed steps or current step
    if (index <= currentStepIndex || stepFeedback[index - 1] === 'correct') {
      onStepChange(index);
      setShowHint(false);
    }
  };

  const resetProblem = () => {
    setStepAnswers(new Array(problem.steps.length).fill(''));
    setStepFeedback(new Array(problem.steps.length).fill(null));
    setShowHint(false);
    setAttempts(0);
    onStepChange(0);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && stepAnswers[currentStepIndex].trim()) {
      checkStepAnswer();
    }
  };

  const allStepsComplete = completedSteps === problem.steps.length;

  return (
    <MathProblemView
      problem={problem}
      currentStepIndex={currentStepIndex}
      stepAnswers={stepAnswers}
      stepFeedback={stepFeedback}
      showHint={showHint}
      attempts={attempts}
      progress={progress}
      completedSteps={completedSteps}
      allStepsComplete={allStepsComplete}
      onStepAnswerChange={updateStepAnswer}
      onCheckAnswer={checkStepAnswer}
      onGoToStep={goToStep}
      onToggleHint={() => setShowHint(!showHint)}
      onReset={resetProblem}
      onKeyDown={handleKeyDown}
    />
  );
}
