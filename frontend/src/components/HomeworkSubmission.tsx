import { useState, useRef } from 'react';
import { toast } from 'sonner';
import { HomeworkSubmissionView, ProcessedResultView } from './views/HomeworkSubmissionView';
import { MathProblem } from './MathProblem';
import { postHomeworkHelpJson } from '../lib/api';

interface HomeworkSubmissionProps {
  onViewProblem: () => void;
}

interface ProcessedProblem {
  id: number;
  title: string;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  category: string;
  question: string;
  steps: Array<{
    stepNumber: number;
    prompt: string;
    expectedAnswer: string;
    hint: string;
  }>;
  explanation: {
    overview: string;
    stepByStep: Array<{
      title: string;
      content: string;
    }>;
    keyTakeaways: string[];
  };
}

export function HomeworkSubmission({ onViewProblem }: HomeworkSubmissionProps) {
  const [textInput, setTextInput] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [pastedImage, setPastedImage] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingProgress, setProcessingProgress] = useState(0);
  const [processedProblem, setProcessedProblem] = useState<ProcessedProblem | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [activeTab, setActiveTab] = useState('type');
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [lastError, setLastError] = useState<string | null>(null);
  const [rawApiResponse, setRawApiResponse] = useState<any>(null);
  const [showExplanation, setShowExplanation] = useState(false);

  const processHomework = async () => {
    if (!textInput.trim()) {
      toast.error('Please type a problem first (file OCR wiring comes next)');
      return;
    }

    setIsProcessing(true);
    setProcessingProgress(20);
    setLastError(null);
    toast.info('Sending to backend...');

    try {
      // Temporary: your backend endpoint expects a uid that exists in DynamoDB.
      // If you already have a bootstrap flow, we should store the real uid here.
      const uid = localStorage.getItem('uid') || 'demo';

      const res = await postHomeworkHelpJson({
        uid,
        text: textInput,
        yearGroup: 9,
        useCache: true,
      });

      setRawApiResponse(res);
      setProcessingProgress(80);

      const tiers = res?.result?.help?.tiers;

      // Parse steps with their expected answers
      const stepsContent = tiers?.steps?.content || [];
      const stepsWithAnswers = stepsContent
        .filter((b: any) => typeof b?.text === 'string' && b.text.trim().length > 0)
        .map((b: any) => ({
          text: b.text,
          expectedAnswer: b.expectedAnswer || '',
        }));

      const hintText: string = (tiers?.hint?.content || [])
        .map((b: any) => (typeof b?.text === 'string' ? b.text : ''))
        .filter((t: string) => t.trim().length > 0)
        .join('\n');

      const overviewText: string = (tiers?.teachback?.content || [])
        .map((b: any) => (typeof b?.text === 'string' ? b.text : ''))
        .filter((t: string) => t.trim().length > 0)
        .join('\n');

      const processed: ProcessedProblem = {
        id: 999,
        title: 'Your Homework Problem',
        difficulty: 'Medium',
        category: (res?.result?.analysis?.subject || 'Maths') as string,
        question: textInput,
        steps: (stepsWithAnswers.length 
          ? stepsWithAnswers 
          : [{ text: 'Read the question carefully and write down what you know.', expectedAnswer: '' }]
        ).map((step: any, idx: number) => ({
          stepNumber: idx + 1,
          prompt: step.text,
          expectedAnswer: step.expectedAnswer,
          hint: hintText || 'Try the next step if you are stuck.',
        })),
        explanation: {
          overview: overviewText || 'Here is a clear explanation of how to approach this problem.',
          stepByStep: [
            {
              title: 'Nudge',
              content: (tiers?.nudge?.content || [])
                .map((b: any) => (typeof b?.text === 'string' ? b.text : ''))
                .filter((t: string) => t.trim().length > 0)
                .join('\n'),
            },
            {
              title: 'Worked',
              content: (tiers?.worked?.content || [])
                .map((b: any) => (typeof b?.text === 'string' ? b.text : ''))
                .filter((t: string) => t.trim().length > 0)
                .join('\n'),
            },
          ],
          keyTakeaways: (res?.result?.analysis?.common_mistakes || []).slice(0, 3),
        },
      };

      setProcessedProblem(processed);
      setProcessingProgress(100);
      toast.success('Problem processed successfully!');
    } catch (e: any) {
      const msg = e?.message || String(e);
      setLastError(msg);
      setProcessingProgress(0);
      toast.error(`Processing failed: ${msg}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFileUpload = (files: FileList | null) => {
    if (!files) return;
    
    const newFiles = Array.from(files).filter(file => {
      const isImage = file.type.startsWith('image/');
      const isPdf = file.type === 'application/pdf';
      return isImage || isPdf;
    });

    if (newFiles.length === 0) {
      toast.error('Please upload images or PDF files only');
      return;
    }

    setUploadedFiles(prev => [...prev, ...newFiles]);
    toast.success(`${newFiles.length} file(s) uploaded`);
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    const items = e.clipboardData?.items;
    if (!items) return;

    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf('image') !== -1) {
        const blob = items[i].getAsFile();
        if (blob) {
          const reader = new FileReader();
          reader.onload = (event) => {
            setPastedImage(event.target?.result as string);
            toast.success('Image pasted successfully');
          };
          reader.readAsDataURL(blob);
        }
      }
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileUpload(e.dataTransfer.files);
  };

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmitAnother = () => {
    setProcessedProblem(null);
    setTextInput('');
    setUploadedFiles([]);
    setPastedImage(null);
  };

  const canSubmit = Boolean(textInput.trim() || uploadedFiles.length > 0 || pastedImage);

  if (processedProblem && !isProcessing) {
    return (
      <ProcessedResultView
        textInput={textInput}
        uploadedFiles={uploadedFiles}
        pastedImage={pastedImage}
        rawApiResponse={rawApiResponse}
        onSubmitAnother={handleSubmitAnother}
        onViewProblem={onViewProblem}
        showExplanation={showExplanation}
        onToggleExplanation={() => setShowExplanation(!showExplanation)}
        explanation={processedProblem.explanation}
        currentStepIndex={currentStepIndex}
        problemPreview={
          <MathProblem
            problem={processedProblem}
            onSolved={() => {}}
            currentStepIndex={currentStepIndex}
            onStepChange={setCurrentStepIndex}
          />
        }
      />
    );
  }

  return (
    <HomeworkSubmissionView
      error={lastError}
      textInput={textInput}
      uploadedFiles={uploadedFiles}
      pastedImage={pastedImage}
      activeTab={activeTab}
      isProcessing={isProcessing}
      processingProgress={processingProgress}
      isDragging={isDragging}
      canSubmit={canSubmit}
      onTextInputChange={setTextInput}
      onFileUpload={handleFileUpload}
      onPaste={handlePaste}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onRemoveFile={removeFile}
      onRemovePastedImage={() => setPastedImage(null)}
      onActiveTabChange={setActiveTab}
      onProcess={processHomework}
      onFileInputClick={() => fileInputRef.current?.click()}
      fileInputRef={fileInputRef}
    />
  );
}
