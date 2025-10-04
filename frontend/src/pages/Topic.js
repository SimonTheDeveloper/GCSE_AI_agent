import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';

export default function Topic() {
  const { topicId } = useParams();
  const navigate = useNavigate();
  const { startQuiz, uid, bootstrap, topicsBySubject, fetchSubjects } = useAppStore();
  const [topic, setTopic] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      // ensure subjects/topics are loaded so we can resolve topic info
      if (!Object.keys(topicsBySubject).length) {
        await fetchSubjects();
      }
      // find topic by id across subjects
      for (const subject of Object.keys(topicsBySubject)) {
        const found = (topicsBySubject[subject] || []).find(t => t.id === topicId);
        if (found) {
          setTopic({ ...found, subject });
          break;
        }
      }
      setLoading(false);
    })();
  }, [topicId, topicsBySubject, fetchSubjects]);

  const onStart = async () => {
    try {
      if (!uid) {
        await bootstrap('browser-device');
      }
      const q = await startQuiz(topicId, 5);
      navigate(`/quiz/${q.quizId}`);
    } catch (e) {
      alert('Unable to start quiz. Please try again.');
      // Optionally log e
    }
  };

  if (loading) return <div className="container" style={{padding:'2rem 0'}}>Loading topic…</div>;
  if (!topic) return <div className="container" style={{padding:'2rem 0'}}>Topic not found.</div>;
  return (
    <div className="section section-padding-02">
      <div className="container">
        <div className="section-title text-center">
          <h2 className="title">{topic.title}</h2>
          <p>Subject: {topic.subject} · ~{topic.estMinutes}m</p>
        </div>
        <div className="text-center">
          <button className="btn btn-primary btn-hover-dark" onClick={onStart}>Start 5-question quiz</button>
        </div>
      </div>
    </div>
  );
}
