import React, { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';

export default function Quiz() {
  const { quizId } = useParams();
  const navigate = useNavigate();
  const { currentQuiz, submitQuiz } = useAppStore();
  const [answers, setAnswers] = useState({});

  const questions = useMemo(() => currentQuiz?.questions || [], [currentQuiz]);

  const progress = useMemo(() => {
    const answered = Object.keys(answers).length;
    const total = questions.length || 1;
    return Math.round((answered / total) * 100);
  }, [answers, questions]);

  const onChoose = (qid, ci) => setAnswers(a => ({ ...a, [qid]: ci }));

  const onSubmit = async () => {
    const payload = Object.entries(answers).map(([questionId, choiceIndex]) => ({ questionId, choiceIndex }));
    const res = await submitQuiz(payload);
    navigate(`/results/${quizId}`, { state: res });
  };

  if (!currentQuiz || currentQuiz.quizId !== quizId) return <div style={{padding:'1rem'}}>No active quiz.</div>;

  return (
    <div style={{padding:'1rem'}}>
      <h1>Quiz</h1>
      <div style={{height:8, background:'#eee', borderRadius:4, margin:'8px 0'}}>
        <div style={{width:`${progress}%`, height:'100%', background:'#4f46e5', borderRadius:4}} />
      </div>
      {questions.map((q) => (
        <div key={q.id} style={{marginBottom:'1rem'}}>
          <div><strong>{q.stem}</strong></div>
          <ul style={{listStyle:'none', padding:0}}>
            {q.choices.map((choice, ci) => (
              <li key={ci}>
                <label>
                  <input type="radio" name={`q-${q.id}`} checked={answers[q.id]===ci} onChange={() => onChoose(q.id, ci)} /> {choice}
                </label>
              </li>
            ))}
          </ul>
        </div>
      ))}
      <button onClick={onSubmit} disabled={Object.keys(answers).length !== questions.length}>Submit</button>
    </div>
  );
}
