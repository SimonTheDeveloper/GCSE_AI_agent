import React, { useEffect, useState } from 'react';
import { useAppStore } from '../store/useAppStore';

export default function Review() {
  const { fetchReviewNext } = useAppStore();
  const [due, setDue] = useState([]);

  useEffect(() => {
    (async () => {
      try {
        const data = await fetchReviewNext();
        setDue(data.due || []);
      } catch (e) { /* ignore */ }
    })();
  }, [fetchReviewNext]);

  return (
    <div style={{padding:'1rem'}}>
      <h1>Review Queue</h1>
      {!due.length ? <p>Nothing due yet.</p> : (
        due.map(group => (
          <div key={group.topicId} style={{marginBottom:'1rem'}}>
            <h3>{group.topicId}</h3>
            <ul>
              {group.cardIds.map(id => <li key={id}>{id}</li>)}
            </ul>
          </div>
        ))
      )}
    </div>
  );
}
