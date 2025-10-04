import { create } from 'zustand';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8001';

export const useAppStore = create((set, get) => ({
  uid: null,
  topicsBySubject: {}, // { subject: [{id,title,estMinutes}] }
  currentQuiz: null,   // { quizId, topicId, questions }

  bootstrap: async (deviceId) => {
    const res = await fetch(`${API_BASE}/api/v1/users/bootstrap`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ deviceId }),
    });
    const data = await res.json();
    set({ uid: data.uid });
    return data;
  },

  fetchSubjects: async () => {
    const res = await fetch(`${API_BASE}/api/v1/subjects`);
    const data = await res.json();
    const map = {};
    data.forEach(s => { map[s.subject] = s.topics; });
    set({ topicsBySubject: map });
    return map;
  },

  startQuiz: async (topicId, numQuestions = 5) => {
    const uid = get().uid;
    if (!uid) throw new Error('No uid');
    const res = await fetch(`${API_BASE}/api/v1/quiz/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ uid, topicId, numQuestions })
    });
    const data = await res.json();
    set({ currentQuiz: data });
    return data;
  },

  submitQuiz: async (answers) => {
    const uid = get().uid;
    const q = get().currentQuiz;
    const res = await fetch(`${API_BASE}/api/v1/quiz/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ uid, quizId: q.quizId, answers })
    });
    const data = await res.json();
    return data;
  },

  fetchReviewNext: async () => {
    const uid = get().uid;
    const res = await fetch(`${API_BASE}/api/v1/review/next?uid=${encodeURIComponent(uid)}`);
    return res.json();
  }
}));
