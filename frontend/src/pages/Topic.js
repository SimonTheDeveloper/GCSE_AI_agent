import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';

export default function Topic() {
  const { topicId } = useParams();
  const navigate = useNavigate();
  const { startQuiz } = useAppStore();
  const [topic, setTopic] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // lightweight fetch of topic cards count/info via store if needed
    setTopic({ id: topicId });
    setLoading(false);
  }, [topicId]);

  const onStart = async () => {
    const q = await startQuiz(topicId, 5);
    navigate(`/quiz/${q.quizId}`);
  };

  if (loading) return <div style={{padding:'1rem'}}>Loading topic…</div>;
  return (
    <div style={{padding:'1rem'}}>
      <h1>Topic</h1>
      <p>Topic ID: {topic.id}</p>
      <button onClick={onStart}>Start 5-question quiz</button>
    </div>
  );
}
