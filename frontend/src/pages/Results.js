import React from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';

export default function Results() {
  const { quizId } = useParams();
  const { state } = useLocation();
  const res = state || { score: 0, breakdown: [], nextSteps: { cardIds: [] } };

  return (
    <div style={{padding:'1rem'}}>
      <h1>Results</h1>
      <p>Quiz {quizId}</p>
      <h2>Score: {res.score}</h2>
      <h3>Weak areas</h3>
      {res.nextSteps?.cardIds?.length ? (
        <ul>
          {res.nextSteps.cardIds.map(id => <li key={id}>{id}</li>)}
        </ul>
      ) : <p>No weak areas detected.</p>}
      <div style={{marginTop:'1rem'}}>
        <Link to="/review">Go to Review</Link>
      </div>
    </div>
  );
}
