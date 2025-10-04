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
    <>
      {/* Hero Area (simplified from theme) */}
      <div className="section hero-section-2">
        <div className="container">
          <div className="row align-items-center g-4">
            <div className="col-lg-7">
              <div className="hero-content">
                <h1 className="title">Ace your GCSEs with smart quizzes and review</h1>
                <p>Start a topic, take a quick quiz, and focus your review where it matters.</p>
                <div className="hero-btn">
                  <Link className="btn btn-primary btn-hover-dark" to="/review">Go to Review Queue</Link>
                </div>
              </div>
            </div>
            <div className="col-lg-5 d-none d-md-block">
              <img src="/theme/edule/assets/images/slider/slider-1.png" alt="Hero" style={{maxWidth:'100%', height:'auto'}} />
            </div>
          </div>
        </div>
      </div>

      {/* Subjects Section */}
      <div id="subjects" className="section section-padding-02">
        <div className="container">
          <div className="section-title text-center">
            <h2 className="title">Pick a Subject</h2>
            <p>Each topic has a short quiz to quickly assess and reinforce.</p>
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
    </>
  );
}
