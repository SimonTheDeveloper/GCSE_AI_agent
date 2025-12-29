import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { CheckCircle2, ChevronLeft, Filter } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";

interface Problem {
  id: number;
  title: string;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  category: string;
}

interface ProblemSelectorProps {
  problems: Problem[];
  allProblems: Problem[];
  currentProblemId: number;
  onSelectProblem: (id: number) => void;
  solvedProblems: number[];
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  difficultyFilter: string;
  onDifficultyFilterChange: (value: string) => void;
  categoryFilter: string;
  onCategoryFilterChange: (value: string) => void;
}

export function ProblemSelector({ 
  problems, 
  allProblems,
  currentProblemId, 
  onSelectProblem, 
  solvedProblems,
  isCollapsed,
  onToggleCollapse,
  difficultyFilter,
  onDifficultyFilterChange,
  categoryFilter,
  onCategoryFilterChange
}: ProblemSelectorProps) {
  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Easy':
        return 'text-green-600';
      case 'Medium':
        return 'text-yellow-600';
      case 'Hard':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  // Get unique categories from all problems
  const categories = ['All', ...Array.from(new Set(allProblems.map(p => p.category)))];
  const difficulties = ['All', 'Easy', 'Medium', 'Hard'];

  return (
    <div className="space-y-3">
      <div className="px-3 pb-2 border-b flex items-center justify-between">
        <h3 className="text-gray-700">Practice Problems</h3>
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleCollapse}
          className="h-7 w-7"
          title="Collapse panel (C)"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
      </div>

      {/* Filters */}
      <div className="px-3 space-y-2">
        <div className="flex items-center gap-2 text-xs text-gray-600 mb-1">
          <Filter className="h-3 w-3" />
          <span>Filters</span>
        </div>
        <Select value={difficultyFilter} onValueChange={onDifficultyFilterChange}>
          <SelectTrigger className="h-8 text-xs">
            <SelectValue placeholder="Difficulty" />
          </SelectTrigger>
          <SelectContent>
            {difficulties.map((diff) => (
              <SelectItem key={diff} value={diff} className="text-xs">
                {diff}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={categoryFilter} onValueChange={onCategoryFilterChange}>
          <SelectTrigger className="h-8 text-xs">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            {categories.map((cat) => (
              <SelectItem key={cat} value={cat} className="text-xs">
                {cat}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Problem List */}
      <div className="space-y-1 px-2">
        {problems.length === 0 ? (
          <div className="px-3 py-4 text-xs text-gray-500 text-center">
            No problems match the selected filters
          </div>
        ) : (
          problems.map((problem) => {
            const problemNumber = allProblems.findIndex(p => p.id === problem.id) + 1;
            return (
              <button
                key={problem.id}
                className={`w-full text-left px-3 py-2.5 rounded-lg transition-all ${
                  currentProblemId === problem.id
                    ? 'bg-blue-500 text-white'
                    : 'hover:bg-gray-100 text-gray-700'
                }`}
                onClick={() => onSelectProblem(problem.id)}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                    currentProblemId === problem.id
                      ? 'bg-white/20 text-white'
                      : 'bg-gray-200 text-gray-700'
                  }`}>
                    {problemNumber}
                  </span>
                  <span className="flex-1 text-sm">{problem.title}</span>
                  {solvedProblems.includes(problem.id) && (
                    <CheckCircle2 className={`h-4 w-4 flex-shrink-0 ${
                      currentProblemId === problem.id ? 'text-white' : 'text-green-600'
                    }`} />
                  )}
                </div>
                <div className="flex items-center gap-2 ml-7">
                  <span className="text-xs opacity-75">{problem.category}</span>
                  <span className="text-xs">•</span>
                  <span className={`text-xs ${
                    currentProblemId === problem.id 
                      ? 'opacity-90' 
                      : getDifficultyColor(problem.difficulty)
                  }`}>
                    {problem.difficulty}
                  </span>
                </div>
              </button>
            );
          })
        )}
      </div>

      {/* Keyboard shortcuts hint */}
      <div className="px-3 pt-2 border-t">
        <div className="text-xs text-gray-500 space-y-1">
          <div className="flex items-center justify-between">
            <span>Navigate:</span>
            <kbd className="px-1.5 py-0.5 bg-gray-100 rounded text-xs">↑↓</kbd>
          </div>
          <div className="flex items-center justify-between">
            <span>Select 1-5:</span>
            <kbd className="px-1.5 py-0.5 bg-gray-100 rounded text-xs">1-5</kbd>
          </div>
          <div className="flex items-center justify-between">
            <span>Toggle explanation:</span>
            <kbd className="px-1.5 py-0.5 bg-gray-100 rounded text-xs">E</kbd>
          </div>
          <div className="flex items-center justify-between">
            <span>Collapse panel:</span>
            <kbd className="px-1.5 py-0.5 bg-gray-100 rounded text-xs">C</kbd>
          </div>
        </div>
      </div>
    </div>
  );
}
