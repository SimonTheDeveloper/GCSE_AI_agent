import React, { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';
import { isAuthenticated } from '../auth';

export default function Quiz() {
  const { quizId } = useParams();
  const navigate = useNavigate();
  const { currentQuiz, submitQuiz, updateProgress } = useAppStore();
  const [answers, setAnswers] = useState({});
  const [currentIdx, setCurrentIdx] = useState(0);
  // Track per-question eliminated options for hints and skipped questions
  const [hiddenChoices, setHiddenChoices] = useState({}); // { [qid]: Set<number> | number[] }
  const [skipped, setSkipped] = useState({}); // { [qid]: true }

  const questions = useMemo(() => currentQuiz?.questions || [], [currentQuiz]);
  const total = questions.length || 0;
  const currentQ = total > 0 ? questions[currentIdx] : null;

  const progress = useMemo(() => {
    const answered = Object.keys(answers).length;
    const denom = total || 1;
    return Math.round((answered / denom) * 100);
  }, [answers, total]);

  const onChoose = (qid, ci) => {
    setAnswers(a => ({ ...a, [qid]: ci }));
    // Clear skipped flag if user selects an answer
    setSkipped(s => {
      if (!s[qid]) return s;
      const copy = { ...s };
      delete copy[qid];
      return copy;
    });
  };

  const onSkip = () => {
    if (!currentQ) return;
    setSkipped(s => ({ ...s, [currentQ.id]: true }));
    setCurrentIdx(i => Math.min(total - 1, i + 1));
  };

  const onHint = () => {
    if (!currentQ) return;
    const qid = currentQ.id;
    const already = hiddenChoices[qid] ? new Set(hiddenChoices[qid]) : new Set();
    // Avoid removing if only two options remain
    const remaining = currentQ.choices
      .map((_, idx) => idx)
      .filter(idx => !already.has(idx));
    if (remaining.length <= 2) return;
    // Choose a wrong option to hide
    const wrongs = remaining.filter(idx => idx !== (currentQ.correctIndex ?? -1));
    if (!wrongs.length) return;
    const pick = wrongs[Math.floor(Math.random() * wrongs.length)];
    already.add(pick);
    setHiddenChoices(h => ({ ...h, [qid]: Array.from(already) }));
  };

  const onSubmit = async () => {
    const totalAnswered = Object.keys(answers).length;
    if (total > 0 && totalAnswered < total) {
      const proceed = window.confirm(`You have ${total - totalAnswered} unanswered question(s). Submit anyway?`);
      if (!proceed) return;
    }
    const payload = Object.entries(answers).map(([questionId, choiceIndex]) => ({ questionId, choiceIndex }));
    const res = await submitQuiz(payload);
    // Record progress if signed in (non-blocking)
    if (isAuthenticated()) {
      try {
        const finalScoreFraction = total > 0 ? (res?.score ?? 0) / total : 0;
        await updateProgress({
          topicId: currentQuiz?.topicId,
          exerciseId: quizId,
          status: 'completed',
          score: finalScoreFraction,
          meta: { total: total, correct: res?.score ?? 0 },
        });
      } catch (e) {
        // Do not block navigation on progress logging errors
      }
    }
 
    // Build client-side meta for skipped vs unanswered
    const allIds = questions.map(q => q.id);
    const answeredIds = Object.keys(answers);
    const skippedIds = Object.keys(skipped);
    const unansweredIds = allIds.filter(id => !answeredIds.includes(id) && !skippedIds.includes(id));
    navigate(`/results/${quizId}`, { state: { ...res, clientSummary: { answeredIds, skippedIds, unansweredIds }, questions, topicId: currentQuiz?.topicId } });
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
              {currentQ.choices.map((choice, ci) => {
                const hidden = (hiddenChoices[currentQ.id] || []).includes(ci);
                if (hidden) return null;
                return (
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
                );
              })}
            </ul>
            {hiddenChoices[currentQ.id]?.length ? (
              <div style={{marginTop:8, color:'#666'}}>Hint used: one wrong option removed.</div>
            ) : null}
            {skipped[currentQ.id] ? (
              <div style={{marginTop:8, color:'#666'}}>You skipped this question.</div>
            ) : null}
          </div>
        )}

        <div style={{display:'flex', gap:8, alignItems:'center'}}>
          <button
            onClick={() => setCurrentIdx(i => Math.max(0, i-1))}
            disabled={currentIdx === 0}
            className="btn btn-outline-secondary"
          >Previous</button>

          <button
            onClick={onSkip}
            disabled={currentIdx >= total - 1}
            className="btn btn-outline-secondary"
          >Skip</button>

          <button
            onClick={onHint}
            disabled={!currentQ || (hiddenChoices[currentQ.id]?.length || 0) >= Math.max(0, (currentQ.choices?.length || 0) - 2)}
            className="btn btn-light"
          >Hint</button>

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
        {currentQ && answers[currentQ.id] === undefined && !skipped[currentQ.id] && (
          <div style={{marginTop:8, color:'#666'}}>Select an answer to continue, or use Skip.</div>
        )}
      </div>
    </div>
  );
}
