import React, { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';

export default function Quiz() {
  const { quizId } = useParams();
  const navigate = useNavigate();
  const { currentQuiz, submitQuiz } = useAppStore();
  const [answers, setAnswers] = useState({});
  const [currentIdx, setCurrentIdx] = useState(0);

  const questions = useMemo(() => currentQuiz?.questions || [], [currentQuiz]);
  const total = questions.length || 0;
  const currentQ = total > 0 ? questions[currentIdx] : null;

  const progress = useMemo(() => {
    const answered = Object.keys(answers).length;
    const denom = total || 1;
    return Math.round((answered / denom) * 100);
  }, [answers, total]);

  const onChoose = (qid, ci) => setAnswers(a => ({ ...a, [qid]: ci }));

  const onSubmit = async () => {
    const totalAnswered = Object.keys(answers).length;
    if (total > 0 && totalAnswered < total) {
      const proceed = window.confirm(`You have ${total - totalAnswered} unanswered question(s). Submit anyway?`);
      if (!proceed) return;
    }
    const payload = Object.entries(answers).map(([questionId, choiceIndex]) => ({ questionId, choiceIndex }));
    const res = await submitQuiz(payload);
    navigate(`/results/${quizId}`, { state: res });
  };

  if (!currentQuiz || currentQuiz.quizId !== quizId) return <div style={{padding:'1rem'}}>No active quiz.</div>;

  return (
    <div className="section section-padding-02">
      <div className="container">
        <div className="section-title text-center">
          <h2 className="title">Quiz</h2>
        </div>
        <div className="progress" style={{height:8, margin:'8px 0 16px'}}>
          <div className="progress-bar" role="progressbar" style={{width:`${progress}%`}} aria-valuenow={progress} aria-valuemin="0" aria-valuemax="100" />
        </div>

        {currentQ && (
          <div key={currentQ.id} className="p-3" style={{marginBottom:'1rem', border:'1px solid #eee', borderRadius:8}}>
            <div style={{marginBottom:8}}><strong>{currentQ.stem}</strong></div>
            <ul style={{listStyle:'none', padding:0, margin:0}}>
              {currentQ.choices.map((choice, ci) => (
                <li key={ci} style={{margin: '6px 0'}}>
                  <label>
                    <input
                      type="radio"
                      name={`q-${currentQ.id}`}
                      checked={answers[currentQ.id]===ci}
                      onChange={() => onChoose(currentQ.id, ci)}
                    />{' '}
                    {choice}
                  </label>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div style={{display:'flex', gap:8}}>
          <button
            onClick={() => setCurrentIdx(i => Math.max(0, i-1))}
            disabled={currentIdx === 0}
            className="btn btn-outline-secondary"
          >Previous</button>

          {currentIdx < total - 1 ? (
            <button
              onClick={() => setCurrentIdx(i => Math.min(total-1, i+1))}
              disabled={currentQ ? answers[currentQ.id] === undefined : true}
              style={{marginLeft:'auto'}}
              className="btn btn-primary btn-hover-dark"
            >Next</button>
          ) : (
            <button
              onClick={onSubmit}
              disabled={Object.keys(answers).length === 0}
              style={{marginLeft:'auto'}}
              className="btn btn-primary btn-hover-dark"
            >Submit</button>
          )}
        </div>
        {currentQ && answers[currentQ.id] === undefined && (
          <div style={{marginTop:8, color:'#666'}}>Select an answer to continue to the next question.</div>
        )}
      </div>
    </div>
  );
}
