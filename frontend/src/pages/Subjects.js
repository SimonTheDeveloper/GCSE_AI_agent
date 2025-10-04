import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';

export default function Subjects() {
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
    <div className="section section-padding-02">
      <div className="container">
        <div className="section-title text-center">
          <h2 className="title">Pick a Subject</h2>
          <p>Choose a subject and start a quick topic quiz to assess and reinforce.</p>
        </div>
        <div className="row g-4">
          {Object.keys(topicsBySubject).map(subject => (
            <div className="col-lg-6" key={subject}>
              <div className="p-3" style={{border:'1px solid #eee', borderRadius:8}}>
                <h3 className="mb-3">{subject}</h3>
                <ul className="list-unstyled mb-0">
                  {topicsBySubject[subject].map(t => (
                    <li key={t.id} className="mb-2">
                      <Link to={`/topics/${t.id}`}>{t.title} · ~{t.estMinutes}m</Link>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
