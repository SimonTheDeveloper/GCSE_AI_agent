import React, { useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';

export default function SubjectsDetail() {
  const { subjectId } = useParams();
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

  const subjectKeys = Object.keys(topicsBySubject);
  const matchedKey = subjectKeys.find(k => k.toLowerCase() === (subjectId || '').toLowerCase());
  const topics = matchedKey ? (topicsBySubject[matchedKey] || []) : [];
  const title = (matchedKey || subjectId || '').replace(/\b\w/g, c => c.toUpperCase());

  return (
    <div className="section section-padding-02">
      <div className="container">
        <div className="section-title text-center">
          <h2 className="title">{title}</h2>
          <p>Pick a topic to start a quick quiz.</p>
        </div>
        <div className="row g-4 justify-content-center">
          <div className="col-lg-8">
            <div className="p-3" style={{border:'1px solid #eee', borderRadius:8}}>
              <ul className="list-unstyled mb-0">
                {topics.map(t => (
                  <li key={t.id} className="mb-2 d-flex justify-content-between align-items-center">
                    <span>{t.title} · ~{t.estMinutes}m</span>
                    <Link className="btn btn-sm btn-primary btn-hover-dark" to={`/topics/${t.id}`}>Open</Link>
                  </li>
                ))}
                {!topics.length && (
                  <li>
                    No topics found for this subject. <Link to="/subjects">Back to all subjects</Link>
                  </li>
                )}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
