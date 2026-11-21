import { Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './layouts/AppLayout.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Profile from './pages/Profile.jsx';
import ExamRecommendation from './pages/ExamRecommendation.jsx';
import Diagnostic from './pages/Diagnostic.jsx';
import StudyPlan from './pages/StudyPlan.jsx';
import AdaptiveQuiz from './pages/AdaptiveQuiz.jsx';
import Performance from './pages/Performance.jsx';
import Resources from './pages/Resources.jsx';
import PYQs from './pages/PYQs.jsx';
import Doubts from './pages/Doubts.jsx';
import Login from './pages/Login.jsx';
import { isLoggedIn } from './services/api.js';

function ProtectedRoute({ children }) {
  return isLoggedIn() ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route
        path="/login"
        element={isLoggedIn() ? <Navigate to="/" replace /> : <Login />}
      />

      <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route index element={<Dashboard />} />
        <Route path="profile" element={<Profile />} />
        <Route path="exam-recommendation" element={<ExamRecommendation />} />
        <Route path="diagnostic" element={<Diagnostic />} />
        <Route path="study-plan" element={<StudyPlan />} />
        <Route path="adaptive-quiz" element={<AdaptiveQuiz />} />
        <Route path="performance" element={<Performance />} />
        <Route path="resources" element={<Resources />} />
        <Route path="pyqs" element={<PYQs />} />
        <Route path="doubts" element={<Doubts />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
