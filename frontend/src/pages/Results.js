import React from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';

export default function Results() {
  const { quizId } = useParams();
  const { state } = useLocation();
  const navigate = useNavigate();
  const { startQuiz } = useAppStore();
  const res = state || { score: 0, breakdown: [], nextSteps: { cardIds: [] } };
  const client = res.clientSummary || { answeredIds: [], skippedIds: [], unansweredIds: [] };
  const questions = res.questions || [];
  const statusOf = (qid) => {
    const b = (res.breakdown || []).find(x => x.questionId === qid);
    if (client.skippedIds.includes(qid)) return 'Skipped';
    if (client.unansweredIds.includes(qid)) return 'Unanswered';
    if (b && b.correct) return 'Correct';
    if (b && !b.correct) return 'Incorrect';
    return 'Answered';
  };

  const retryIncorrect = async () => {
    // If backend supports targeted drill by cardIds, we would call that.
    // For now, reuse the same topic with a small quiz size (e.g., 3-5)
    const topicId = res.topicId;
    if (!topicId) return alert('Topic not available for retry.');
    const count = Math.min(5, (res.nextSteps?.cardIds?.length || 5) || 5);
    const q = await startQuiz(topicId, count);
    navigate(`/quiz/${q.quizId}`);
  };

  const retrySkipped = async () => {
    const topicId = res.topicId;
    if (!topicId) return alert('Topic not available for retry.');
    const count = Math.min(5, client.skippedIds.length || 5);
    const q = await startQuiz(topicId, count);
    navigate(`/quiz/${q.quizId}`);
  };

  return (
    <div className="section section-padding-02">
      <div className="container">
        <div className="section-title text-center">
          <h2 className="title">Results</h2>
          <p>Quiz {quizId}</p>
        </div>
        <div className="row g-4 justify-content-center">
          <div className="col-lg-8">
            <div className="p-3" style={{border:'1px solid #eee', borderRadius:8}}>
              <h4 className="mb-3">Score: {res.score}</h4>
              <div className="row text-center">
                <div className="col">
                  <div className="p-2"><strong>Answered</strong><div>{client.answeredIds.length}</div></div>
                </div>
                <div className="col">
                  <div className="p-2"><strong>Skipped</strong><div>{client.skippedIds.length}</div></div>
                </div>
                <div className="col">
                  <div className="p-2"><strong>Unanswered</strong><div>{client.unansweredIds.length}</div></div>
                </div>
              </div>

              <h5 className="mt-3">Per-question breakdown</h5>
              {questions.length ? (
                <ul className="list-unstyled">
                  {questions.map((q, idx) => (
                    <li key={q.id} className="mb-2 d-flex justify-content-between align-items-center">
                      <span>Q{idx+1}: {q.stem}</span>
                      <span className="badge bg-secondary">{statusOf(q.id)}</span>
                    </li>
                  ))}
                </ul>
              ) : null}

              <h5 className="mt-3">Weak areas</h5>
              {res.nextSteps?.cardIds?.length ? (
                <ul>
                  {res.nextSteps.cardIds.map(id => <li key={id}>{id}</li>)}
                </ul>
              ) : <p>No weak areas detected.</p>}

              <div className="d-flex gap-2" style={{marginTop:'1rem'}}>
                <button className="btn btn-outline-secondary" onClick={retrySkipped} disabled={!client.skippedIds.length}>Retry Skipped</button>
                <button className="btn btn-outline-secondary" onClick={retryIncorrect} disabled={!(res.nextSteps?.cardIds?.length)}>
                  Retry Incorrect
                </button>
                <Link className="btn btn-primary btn-hover-dark ms-auto" to="/review">Go to Review</Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
