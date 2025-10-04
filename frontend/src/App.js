import React from "react";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import './App.css';

import Home from './pages/Home';
import Topic from './pages/Topic';
import Quiz from './pages/Quiz';
import Results from './pages/Results';
import Review from './pages/Review';

function App() {
  return (
    <BrowserRouter>
      <div className="App" style={{padding:'0 1rem'}}>
        <nav style={{display:'flex', gap:12, padding:'0.5rem 0'}}>
          <Link to="/">Home</Link>
          <Link to="/review">Review</Link>
        </nav>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/topics/:topicId" element={<Topic />} />
          <Route path="/quiz/:quizId" element={<Quiz />} />
          <Route path="/results/:quizId" element={<Results />} />
          <Route path="/review" element={<Review />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
