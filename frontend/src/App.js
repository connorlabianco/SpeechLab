import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Header from './components/layout/Header';
import Footer from './components/layout/Footer';
import ProtectedRoute from './components/ProtectedRoute';
import HomeLanding from './pages/HomeLanding';
import Dashboard from './pages/Dashboard';
import Analysis from './pages/Analysis';
import PracticeAnalysis from './pages/PracticeAnalysis';
import History from './pages/History';
import Practice from './pages/Practice';
import Login from './pages/Login';
import NotFound from './pages/NotFound';
import './styles/App.css';

function AppContent() {
  const [analysisData, setAnalysisData] = useState(null);
  
  const handleAnalysisComplete = (data) => {
    setAnalysisData(data);
  };

  return (
    <div className="app">
      <Header />
      <main className="main-content">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<HomeLanding />} />
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/analysis" 
            element={
              <ProtectedRoute>
                <Analysis analysisData={analysisData} />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/analysis/:id" 
            element={
              <ProtectedRoute>
                <Analysis analysisData={analysisData} />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/history" 
            element={
              <ProtectedRoute>
                <History />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/practice" 
            element={
              <ProtectedRoute>
                <Practice />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/practice-analysis/:id" 
            element={
              <ProtectedRoute>
                <PracticeAnalysis />
              </ProtectedRoute>
            } 
          />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
}

export default App;
