import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import './App.css';

import Home from './pages/Home';
import Topic from './pages/Topic';
import Quiz from './pages/Quiz';
import Results from './pages/Results';
import Review from './pages/Review';
import Subjects from './pages/Subjects';
import SubjectsDetail from './pages/SubjectsDetail';
import Homework from './pages/Homework';
import RequireAuth from './components/RequireAuth';
import LayoutSite from './layouts/LayoutSite';
import AppBootstrap from './components/AppBootstrap';

function App() {
  return (
    <BrowserRouter>
      <LayoutSite>
        <AppBootstrap>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/subjects" element={<Subjects />} />
            <Route path="/subjects/:subjectId" element={<SubjectsDetail />} />
            <Route path="/topics/:topicId" element={<Topic />} />
            <Route path="/quiz/:quizId" element={<Quiz />} />
            <Route path="/results/:quizId" element={<Results />} />
            <Route path="/review" element={<Review />} />
            <Route path="/homework" element={<RequireAuth><Homework /></RequireAuth>} />
          </Routes>
        </AppBootstrap>
      </LayoutSite>
    </BrowserRouter>
  );
}

export default App;
