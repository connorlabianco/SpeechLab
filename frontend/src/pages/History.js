import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAnalyses } from '../services/api';
import '../styles/pages/History.css';

function History() {
  const [analyses, setAnalyses] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchAnalyses();
  }, []);

  const fetchAnalyses = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await getAnalyses();
      setAnalyses(response.analyses || []);
    } catch (err) {
      console.error('Error fetching analyses:', err);
      setError('Failed to load your analysis history. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewAnalysis = (analysisId) => {
    navigate(`/analysis/${analysisId}`);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown date';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (isLoading) {
    return (
      <div className="history-page">
        <div className="loading">Loading your analysis history...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="history-page">
        <div className="error-message">{error}</div>
        <button onClick={fetchAnalyses} className="btn-retry">Try Again</button>
      </div>
    );
  }

  return (
    <div className="history-page">
      {/* Base44 gradient background elements */}
      <div className="gradient-bg"></div>
      <div className="gradient-overlay"></div>
      <div className="orb orb1"></div>
      <div className="orb orb2"></div>
      <div className="orb orb3"></div>
      <div className="orb orb4"></div>
      <div className="grain"></div>

      <div className="history-header">
        <h1>Analysis History</h1>
        <p className="subtitle">View and manage your past speech analyses</p>
      </div>

      {analyses.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📊</div>
          <h2>No analyses yet</h2>
          <p>Upload a video to get started with your first speech analysis!</p>
          <button 
            onClick={() => navigate('/')} 
            className="btn-primary"
          >
            Upload Video
          </button>
        </div>
      ) : (
        <div className="analyses-grid">
          {analyses.map((analysis) => (
            <div key={analysis.id} className="analysis-card">
              <div className="card-header">
                <h3 className="card-title">
                  {analysis.filename || `Analysis #${analysis.id}`}
                </h3>
                <span className="card-date">{formatDate(analysis.created_at)}</span>
              </div>
              
              <div className="card-metrics">
                <div className="metric">
                  <span className="metric-label">Duration</span>
                  <span className="metric-value">{formatDuration(analysis.duration)}</span>
                </div>
                <div className="metric">
                  <span className="metric-label">Dominant Emotion</span>
                  <span className="metric-value emotion-badge">
                    {analysis.dominant_emotion || 'N/A'}
                  </span>
                </div>
                <div className="metric">
                  <span className="metric-label">Avg Words/Sec</span>
                  <span className="metric-value">
                    {analysis.avg_wps ? analysis.avg_wps.toFixed(1) : 'N/A'}
                  </span>
                </div>
                <div className="metric">
                  <span className="metric-label">Clarity Score</span>
                  <span className="metric-value">
                    {analysis.clarity_score ? `${analysis.clarity_score.toFixed(0)}%` : 'N/A'}
                  </span>
                </div>
              </div>

              <button
                onClick={() => handleViewAnalysis(analysis.id)}
                className="btn-view-analysis"
              >
                View Full Analysis →
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default History;
