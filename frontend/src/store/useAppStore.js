import { create } from 'zustand';
import { authHeader } from '../auth';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8001';

export const useAppStore = create((set, get) => ({
  uid: null,
  topicsBySubject: {}, // { subject: [{id,title,estMinutes}] }
  currentQuiz: null,   // { quizId, topicId, questions }

  bootstrap: async (deviceId) => {
    let res, data;
    try {
      res = await fetch(`${API_BASE}/api/v1/users/bootstrap`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeader() },
        body: JSON.stringify({ deviceId }),
      });
    } catch (err) {
  console.error('Bootstrap network error:', err);
  throw new Error(`Unable to reach API at ${API_BASE}. Is the backend running?`);
    }
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Bootstrap failed: ${res.status} ${res.statusText} - ${text}`);
    }
    data = await res.json();
    set({ uid: data.uid });
    return data;
  },

  fetchSubjects: async () => {
    let res, data;
    try {
  res = await fetch(`${API_BASE}/api/v1/subjects`, { headers: { ...authHeader() } });
    } catch (err) {
  console.error('fetchSubjects network error:', err);
  throw new Error(`Unable to reach API at ${API_BASE}. Is the backend running?`);
    }
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Fetch subjects failed: ${res.status} ${res.statusText} - ${text}`);
    }
    data = await res.json();
    const map = {};
    data.forEach(s => { map[s.subject] = s.topics; });
    set({ topicsBySubject: map });
    return map;
  },

  startQuiz: async (topicId, numQuestions = 5) => {
    const uid = get().uid;
  if (!uid) throw new Error('No uid');
    let res, data;
    try {
      res = await fetch(`${API_BASE}/api/v1/quiz/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeader() },
        body: JSON.stringify({ uid, topicId, numQuestions })
      });
    } catch (err) {
  console.error('startQuiz network error:', err);
  throw new Error(`Unable to reach API at ${API_BASE}. Is the backend running?`);
    }
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Start quiz failed: ${res.status} ${res.statusText} - ${text}`);
    }
    data = await res.json();
    set({ currentQuiz: data });
    return data;
  },

  submitQuiz: async (answers) => {
    const uid = get().uid;
    const q = get().currentQuiz;
    if (!uid) throw new Error('No uid');
    if (!q || !q.quizId) throw new Error('No active quiz to submit. Please start a new quiz.');
    let res, data;
    try {
      res = await fetch(`${API_BASE}/api/v1/quiz/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeader() },
        body: JSON.stringify({ uid, quizId: q.quizId, answers })
      });
    } catch (err) {
      console.error('submitQuiz network error:', err);
      throw new Error(`Unable to reach API at ${API_BASE}. Is the backend running?`);
    }
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Submit quiz failed: ${res.status} ${res.statusText} - ${text}`);
    }
    data = await res.json();
    return data;
  },

  fetchReviewNext: async () => {
    const uid = get().uid;
    let res;
    try {
  res = await fetch(`${API_BASE}/api/v1/review/next?uid=${encodeURIComponent(uid)}`, { headers: { ...authHeader() } });
    } catch (err) {
  console.error('fetchReviewNext network error:', err);
  throw new Error(`Unable to reach API at ${API_BASE}. Is the backend running?`);
    }
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Fetch review failed: ${res.status} ${res.statusText} - ${text}`);
    }
    return res.json();
  },

  me: async () => {
    let res;
    try {
      res = await fetch(`${API_BASE}/api/v1/me`, { headers: { ...authHeader() } });
    } catch (err) {
      console.error('me network error:', err);
      throw new Error(`Unable to reach API at ${API_BASE}. Is the backend running?`);
    }
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`me failed: ${res.status} ${res.statusText} - ${text}`);
    }
    return res.json();
  }
}));
