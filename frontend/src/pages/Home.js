import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';

export default function Home() {
  const { uid, bootstrap, topicsBySubject, fetchSubjects } = useAppStore();

  useEffect(() => {
    (async () => {
      if (!uid) {
        try { await bootstrap('browser-device'); } catch {}
      }
      if (!Object.keys(topicsBySubject).length) {
        await fetchSubjects();
      }
    })();
  }, [uid, topicsBySubject, bootstrap, fetchSubjects]);

  return (
    <div style={{padding:'1rem'}}>
      <h1>Home</h1>
      <p>Continue review or pick a subject.</p>
      {Object.keys(topicsBySubject).map(subject => (
        <div key={subject} style={{marginTop:'1rem'}}>
          <h2>{subject}</h2>
          <ul>
            {topicsBySubject[subject].map(t => (
              <li key={t.id}>
                <Link to={`/topics/${t.id}`}>{t.title} · ~{t.estMinutes}m</Link>
              </li>
            ))}
          </ul>
        </div>
      ))}
      <div style={{marginTop:'2rem'}}>
        <Link to="/review">Go to Review Queue</Link>
      </div>
    </div>
  );
}
