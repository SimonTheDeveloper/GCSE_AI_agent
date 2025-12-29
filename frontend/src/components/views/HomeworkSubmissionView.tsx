import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { Textarea } from '../ui/textarea';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { 
  Upload, 
  Image as ImageIcon, 
  FileText, 
  Sparkles, 
  CheckCircle2,
  Loader2,
  X,
  ArrowRight
} from 'lucide-react';

export interface HomeworkSubmissionViewProps {
  // Input state
  textInput: string;
  uploadedFiles: File[];
  pastedImage: string | null;
  activeTab: string;
  
  // Processing state
  isProcessing: boolean;
  processingProgress: number;
  
  // UI state
  isDragging: boolean;
  canSubmit: boolean;
  
  // Handlers
  onTextInputChange: (value: string) => void;
  onFileUpload: (files: FileList | null) => void;
  onPaste: (e: React.ClipboardEvent) => void;
  onDragOver: (e: React.DragEvent) => void;
  onDragLeave: () => void;
  onDrop: (e: React.DragEvent) => void;
  onRemoveFile: (index: number) => void;
  onRemovePastedImage: () => void;
  onActiveTabChange: (value: string) => void;
  onProcess: () => void;
  onFileInputClick: () => void;
  
  // Refs
  fileInputRef: React.RefObject<HTMLInputElement>;
  
  // Processed result (if shown from parent)
  children?: React.ReactNode;
}

export function HomeworkSubmissionView({
  textInput,
  uploadedFiles,
  pastedImage,
  activeTab,
  isProcessing,
  processingProgress,
  isDragging,
  canSubmit,
  onTextInputChange,
  onFileUpload,
  onPaste,
  onDragOver,
  onDragLeave,
  onDrop,
  onRemoveFile,
  onRemovePastedImage,
  onActiveTabChange,
  onProcess,
  onFileInputClick,
  fileInputRef,
  children
}: HomeworkSubmissionViewProps) {
  // If children are provided, it means the processed result is being shown
  if (children) {
    return <>{children}</>;
  }

  return (
    <div className="container mx-auto px-6 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="mb-3">Submit Your Homework</h1>
          <p className="text-lg text-gray-600">
            Upload files, paste screenshots, or type your problem. Our AI will convert it into an interactive step-by-step solution.
          </p>
        </div>

        {isProcessing ? (
          <Card className="p-12">
            <div className="text-center">
              <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Loader2 className="h-8 w-8 text-blue-600 animate-spin" />
              </div>
              <h2 className="mb-2">Processing Your Homework</h2>
              <p className="text-gray-600 mb-6">Our AI is analyzing your problem and creating interactive steps...</p>
              <Progress value={processingProgress} className="mb-2" />
              <p className="text-sm text-gray-500">{processingProgress}% complete</p>
            </div>
          </Card>
        ) : (
          <>
            <Card className="p-6 mb-6">
              <div>
                <label className="block mb-2">Enter your math problem</label>
                <p className="text-sm text-gray-500 mb-3">
                  Type your problem, drag & drop files, or paste a screenshot (Ctrl+V / ⌘+V)
                </p>
                
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept="image/*,.pdf"
                  onChange={(e) => onFileUpload(e.target.files)}
                  className="hidden"
                />
                
                <div
                  onDragOver={onDragOver}
                  onDragLeave={onDragLeave}
                  onDrop={onDrop}
                  onPaste={onPaste}
                  className={`relative border-2 border-dashed rounded-lg transition-colors ${
                    isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 focus-within:border-blue-500'
                  }`}
                >
                  <Textarea
                    placeholder="Example: Solve for x: 2x + 5 = 17&#10;&#10;Type your problem here, or drag & drop files, or paste screenshots..."
                    value={textInput}
                    onChange={(e) => onTextInputChange(e.target.value)}
                    className="min-h-[200px] border-0 focus-visible:ring-0 resize-none"
                  />
                  
                  {!textInput && uploadedFiles.length === 0 && !pastedImage && (
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                      <div className="text-center text-gray-400">
                        <div className="flex gap-4 items-center justify-center mb-2">
                          <FileText className="h-5 w-5" />
                          <Upload className="h-5 w-5" />
                          <ImageIcon className="h-5 w-5" />
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Display pasted image */}
                {pastedImage && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <ImageIcon className="h-4 w-4 text-gray-600" />
                        <span className="text-sm">Pasted screenshot</span>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={onRemovePastedImage}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                    <img src={pastedImage} alt="Pasted" className="max-h-64 rounded border" />
                  </div>
                )}

                {/* Display uploaded files */}
                {uploadedFiles.length > 0 && (
                  <div className="mt-4 space-y-2">
                    <p className="text-sm">Uploaded files:</p>
                    {uploadedFiles.map((file, index) => (
                      <div key={index} className="flex items-center justify-between bg-gray-50 p-3 rounded">
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-gray-600" />
                          <span className="text-sm">{file.name}</span>
                          <Badge variant="outline" className="text-xs">
                            {(file.size / 1024).toFixed(1)} KB
                          </Badge>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            onRemoveFile(index);
                          }}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}

                {/* Click to browse files button */}
                <div className="mt-3 flex gap-2 items-center">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={onFileInputClick}
                    className="gap-2"
                  >
                    <Upload className="h-4 w-4" />
                    Browse files
                  </Button>
                  <span className="text-xs text-gray-500">or drag & drop anywhere above</span>
                </div>
              </div>
            </Card>

            <Card className="p-6 bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
              <div className="flex items-start gap-4">
                <div className="bg-blue-500 p-3 rounded-lg">
                  <Sparkles className="h-6 w-6 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="mb-2">AI-Powered Analysis</h3>
                  <p className="text-sm text-gray-700 mb-4">
                    Our AI will analyze your homework and create an interactive step-by-step solution with:
                  </p>
                  <ul className="text-sm text-gray-700 space-y-1 mb-4">
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      Detailed step-by-step breakdown
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      Interactive validation for each step
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      Helpful hints when you're stuck
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      Comprehensive explanations
                    </li>
                  </ul>
                  <Button 
                    onClick={onProcess}
                    disabled={!canSubmit}
                    size="lg"
                    className="gap-2"
                  >
                    <Sparkles className="h-5 w-5" />
                    Process with AI
                  </Button>
                </div>
              </div>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}

// Processed result view component
export interface ProcessedResultViewProps {
  textInput: string;
  uploadedFiles: File[];
  pastedImage: string | null;
  onSubmitAnother: () => void;
  onViewProblem: () => void;
  problemPreview: React.ReactNode;
}

export function ProcessedResultView({
  textInput,
  uploadedFiles,
  pastedImage,
  onSubmitAnother,
  onViewProblem,
  problemPreview
}: ProcessedResultViewProps) {
  return (
    <div className="container mx-auto px-6 py-8">
      <Card className="p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="bg-green-100 p-2 rounded-lg">
              <CheckCircle2 className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <h2>Problem Processed Successfully!</h2>
              <p className="text-sm text-gray-600">Your homework has been converted into step-by-step format</p>
            </div>
          </div>
          <Button variant="outline" onClick={onSubmitAnother}>
            Submit Another Problem
          </Button>
        </div>
      </Card>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="mb-4">Original Submission</h3>
          {textInput && (
            <div className="mb-4">
              <Badge className="mb-2">Text Input</Badge>
              <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded">{textInput}</p>
            </div>
          )}
          {uploadedFiles.length > 0 && (
            <div className="mb-4">
              <Badge className="mb-2">Uploaded Files</Badge>
              <div className="space-y-2">
                {uploadedFiles.map((file, idx) => (
                  <div key={idx} className="text-sm text-gray-700 bg-gray-50 p-2 rounded flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    {file.name}
                  </div>
                ))}
              </div>
            </div>
          )}
          {pastedImage && (
            <div>
              <Badge className="mb-2">Pasted Screenshot</Badge>
              <img src={pastedImage} alt="Pasted" className="rounded border max-h-64 w-auto" />
            </div>
          )}
        </Card>

        <Card className="p-6" id="interactive-preview">
          <div className="mb-4 flex items-center justify-between">
            <h3>Interactive Problem</h3>
            <Button onClick={onViewProblem} className="gap-2">
              Open in Practice Mode
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg border">
            <p className="text-sm text-gray-600 mb-3">
              Preview of your interactive problem. Click "Open in Practice Mode" to work through it with full features.
            </p>
            {problemPreview}
          </div>
        </Card>
      </div>
    </div>
  );
}