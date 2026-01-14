import { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { mathProblems } from './test_data/mathProblems';
import { MathProblem } from './components/MathProblem';
import { ExplanationPanel } from './components/ExplanationPanel';
import { ProblemSelector } from './components/ProblemSelector';
import { Homepage } from './components/Homepage';
import { HomeworkSubmission } from './components/HomeworkSubmission';
import { Navigation } from './components/Navigation';
import { Login } from './components/Login';
import { SignUp } from './components/SignUp';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from './components/ui/resizable';
import { Button } from './components/ui/button';
import { Toaster } from './components/ui/sonner';
import { BookOpen, XCircle, Home } from 'lucide-react';
import { toast } from 'sonner';

 

type AuthView = 'login' | 'signup';

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [authView, setAuthView] = useState<AuthView>('login');
  const [currentProblemId, setCurrentProblemId] = useState(1);
  const [showExplanation, setShowExplanation] = useState(false);
  const [solvedProblems, setSolvedProblems] = useState<number[]>([]);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isPanelCollapsed, setIsPanelCollapsed] = useState(false);
  const [difficultyFilter, setDifficultyFilter] = useState<string>('All');
  const [categoryFilter, setCategoryFilter] = useState<string>('All');

  // Check for existing login state on mount
  useEffect(() => {
    const loggedIn = localStorage.getItem('isLoggedIn') === 'true';
    setIsLoggedIn(loggedIn);
  }, []);

  const currentProblem = mathProblems.find(p => p.id === currentProblemId)!;

  // Filter problems based on selected filters
  const filteredProblems = mathProblems.filter(problem => {
    const matchesDifficulty = difficultyFilter === 'All' || problem.difficulty === difficultyFilter;
    const matchesCategory = categoryFilter === 'All' || problem.category === categoryFilter;
    return matchesDifficulty && matchesCategory;
  });

  const handleProblemSolved = (problemId: number) => {
    if (!solvedProblems.includes(problemId)) {
      setSolvedProblems([...solvedProblems, problemId]);
    }
  };

  const handleProblemChange = (id: number) => {
    setCurrentProblemId(id);
    setCurrentStepIndex(0);
    setShowExplanation(false);
  };

  const handleLogin = () => {
    setIsLoggedIn(true);
    const userName = localStorage.getItem('userName');
    if (userName) {
      toast.success(`Welcome back, ${userName.split(' ')[0]}! Ready to learn?`);
    } else {
      toast.success('Welcome back! Ready to learn?');
    }
  };

  const handleSignUp = () => {
    setIsLoggedIn(true);
    const userName = localStorage.getItem('userName');
    toast.success(`Welcome to GCSE Math Tutor, ${userName?.split(' ')[0] || 'there'}! Let's start learning.`);
  };

  const handleLogout = () => {
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('userName');
    localStorage.removeItem('userGradeLevel');
    localStorage.removeItem('rememberMe');
    setIsLoggedIn(false);
    setAuthView('login');
    navigate('/');
    toast.success('Logged out successfully');
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Only handle shortcuts if not typing in an input
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      // Number keys 1-5 to select problems
      if (e.key >= '1' && e.key <= '5') {
        const problemNum = parseInt(e.key);
        if (mathProblems[problemNum - 1]) {
          handleProblemChange(mathProblems[problemNum - 1].id);
          toast.success(`Switched to Problem ${problemNum}`);
        }
      }

      // Arrow keys to navigate between problems
      if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
        e.preventDefault();
        const currentIndex = filteredProblems.findIndex(p => p.id === currentProblemId);
        let newIndex;
        
        if (e.key === 'ArrowUp') {
          newIndex = currentIndex > 0 ? currentIndex - 1 : filteredProblems.length - 1;
        } else {
          newIndex = currentIndex < filteredProblems.length - 1 ? currentIndex + 1 : 0;
        }
        
        handleProblemChange(filteredProblems[newIndex].id);
      }

      // 'e' to toggle explanation
      if (e.key === 'e' && !e.ctrlKey && !e.metaKey) {
        setShowExplanation(prev => !prev);
      }

      // 'c' to collapse/expand panel
      if (e.key === 'c' && !e.ctrlKey && !e.metaKey) {
        setIsPanelCollapsed(prev => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [currentProblemId, filteredProblems]);

  // Show login or signup page if not authenticated
  if (!isLoggedIn) {
    return (
      <>
        {authView === 'login' ? (
          <Login 
            onLoginSuccess={handleLogin}
            onSignUpClick={() => setAuthView('signup')}
          />
        ) : (
          <SignUp
            onSignUpSuccess={handleSignUp}
            onLoginClick={() => setAuthView('login')}
          />
        )}
        <Toaster position="bottom-right" />
      </>
    );
  }

  return (
    <Routes>
      <Route path="/" element={
        <div className="min-h-screen">
          <div className="bg-white border-b sticky top-0 z-50">
            <div className="container mx-auto px-6 py-4">
              <Navigation 
                onLogoClick={() => navigate('/')} 
                onHomeworkClick={() => navigate('/homework')}
                onLogout={handleLogout}
              />
            </div>
          </div>
          <Homepage onStartPractice={() => navigate('/practice')} />
          <Toaster position="bottom-right" />
        </div>
      } />
      
      <Route path="/homework" element={
        <div className="min-h-screen bg-gray-50">
          <div className="bg-white border-b sticky top-0 z-50">
            <div className="container mx-auto px-6">
              <Navigation 
                onLogoClick={() => navigate('/')} 
                onHomeworkClick={() => navigate('/homework')}
                onLogout={handleLogout}
              />
            </div>
          </div>
          <HomeworkSubmission onViewProblem={() => navigate('/practice')} />
          <Toaster position="bottom-right" />
        </div>
      } />

      <Route path="/practice" element={
        <div className="min-h-screen bg-gray-50">
          <div className="bg-white border-b sticky top-0 z-50">
            <div className="container mx-auto px-6">
              <Navigation 
                onLogoClick={() => navigate('/')} 
                onHomeworkClick={() => navigate('/homework')}
                onLogout={handleLogout}
              />
            </div>
          </div>

          <div className="container mx-auto px-6 py-6">
        <ResizablePanelGroup direction="horizontal" className="min-h-[calc(100vh-120px)] rounded-lg border bg-white">
          {!isPanelCollapsed && (
            <>
              <ResizablePanel defaultSize={18} minSize={15} maxSize={25}>
                <div className="h-full py-4 overflow-auto">
                  <ProblemSelector
                    problems={filteredProblems}
                    allProblems={mathProblems}
                    currentProblemId={currentProblemId}
                    onSelectProblem={handleProblemChange}
                    solvedProblems={solvedProblems}
                    isCollapsed={isPanelCollapsed}
                    onToggleCollapse={() => setIsPanelCollapsed(!isPanelCollapsed)}
                    difficultyFilter={difficultyFilter}
                    onDifficultyFilterChange={setDifficultyFilter}
                    categoryFilter={categoryFilter}
                    onCategoryFilterChange={setCategoryFilter}
                  />
                </div>
              </ResizablePanel>

              <ResizableHandle withHandle />
            </>
          )}

          {isPanelCollapsed && (
            <div className="w-12 border-r flex flex-col items-center py-4 gap-2 bg-gray-50">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsPanelCollapsed(false)}
                className="h-8 w-8"
                title="Expand panel (C)"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="m9 18 6-6-6-6" />
                </svg>
              </Button>
              {mathProblems.map((problem, idx) => (
                <button
                  key={problem.id}
                  onClick={() => handleProblemChange(problem.id)}
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-xs transition-colors ${
                    currentProblemId === problem.id
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                  title={problem.title}
                >
                  {idx + 1}
                </button>
              ))}
            </div>
          )}

          <ResizablePanel defaultSize={isPanelCollapsed ? (showExplanation ? 70 : 100) : (showExplanation ? 52 : 82)} minSize={30}>
            <div className="h-full p-6 overflow-auto">
              <div className="mb-4 flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate('/')}
                    className="gap-2"
                  >
                    <Home className="h-4 w-4" />
                    Home
                  </Button>
                  <div className="h-6 w-px bg-gray-300"></div>
                  <h2>Problem Workspace</h2>
                </div>
                <Button
                  variant={showExplanation ? "destructive" : "default"}
                  onClick={() => setShowExplanation(!showExplanation)}
                  className="gap-2"
                >
                  {showExplanation ? (
                    <>
                      <XCircle className="h-4 w-4" />
                      Hide Explanation
                    </>
                  ) : (
                    <>
                      <BookOpen className="h-4 w-4" />
                      Show Explanation
                    </>
                  )}
                </Button>
              </div>
              <MathProblem
                problem={currentProblem}
                onSolved={handleProblemSolved}
                currentStepIndex={currentStepIndex}
                onStepChange={setCurrentStepIndex}
              />
            </div>
          </ResizablePanel>

          {showExplanation && (
            <>
              <ResizableHandle withHandle />
              <ResizablePanel defaultSize={30} minSize={25} maxSize={45}>
                <div className="h-full overflow-hidden">
                  <ExplanationPanel 
                    explanation={currentProblem.explanation} 
                    currentStepIndex={currentStepIndex}
                  />
                </div>
              </ResizablePanel>
            </>
          )}
        </ResizablePanelGroup>
          </div>
          <Toaster position="bottom-right" />
        </div>
      } />
    </Routes>
  );
}
