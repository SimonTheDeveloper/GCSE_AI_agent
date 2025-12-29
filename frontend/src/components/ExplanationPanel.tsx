import { Card } from "./ui/card";
import { ScrollArea } from "./ui/scroll-area";
import { BookOpen } from 'lucide-react';

interface ExplanationStep {
  step: number;
  title: string;
  content: string;
  formula?: string;
}

interface ExplanationPanelProps {
  explanation: {
    concept: string;
    steps: ExplanationStep[];
    hint: string;
  };
  currentStepIndex: number;
}

export function ExplanationPanel({ explanation, currentStepIndex }: ExplanationPanelProps) {
  return (
    <Card className="h-full flex flex-col">
      <div className="p-4 border-b bg-blue-50">
        <div className="flex items-center gap-2">
          <BookOpen className="h-5 w-5 text-blue-600" />
          <h3 className="text-blue-900">Step-by-Step Explanation</h3>
        </div>
      </div>
      
      <ScrollArea className="flex-1 p-6">
        <div className="space-y-6">
          <div>
            <h4 className="text-blue-600 mb-2">Concept</h4>
            <p className="text-gray-700">{explanation.concept}</p>
          </div>

          <div className="space-y-4">
            <h4 className="text-blue-600">Solution Steps</h4>
            {explanation.steps.map((step, index) => (
              <Card 
                key={step.step} 
                className={`p-4 transition-all ${
                  index === currentStepIndex 
                    ? 'bg-blue-50 border-2 border-blue-400 shadow-md' 
                    : index < currentStepIndex
                    ? 'bg-green-50 border border-green-200'
                    : 'bg-gray-50 opacity-60'
                }`}
              >
                <div className="flex gap-3">
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full text-white flex items-center justify-center ${
                    index === currentStepIndex 
                      ? 'bg-blue-600 ring-4 ring-blue-200' 
                      : index < currentStepIndex
                      ? 'bg-green-600'
                      : 'bg-gray-400'
                  }`}>
                    {step.step}
                  </div>
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-2">
                      <h5>{step.title}</h5>
                      {index === currentStepIndex && (
                        <span className="px-2 py-0.5 bg-blue-600 text-white text-xs rounded">
                          Current Step
                        </span>
                      )}
                    </div>
                    <p className="text-gray-700">{step.content}</p>
                    {step.formula && (
                      <div className="p-3 bg-white rounded border border-gray-200 font-mono text-center">
                        {step.formula}
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>

          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <h4 className="text-yellow-800 mb-2">💡 Overall Hint</h4>
            <p className="text-yellow-700">{explanation.hint}</p>
          </div>
        </div>
      </ScrollArea>
    </Card>
  );
}
