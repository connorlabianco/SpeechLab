import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAnalyses, getPracticeSessions } from '../services/api';
import '../styles/pages/History.css';

function History() {
  const [analyses, setAnalyses] = useState([]);
  const [practiceSessions, setPracticeSessions] = useState([]);
  const [activeTab, setActiveTab] = useState('analyses'); // 'analyses' or 'practice'
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchAllHistory();
  }, []);

  const fetchAllHistory = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Fetch both in parallel
      const [analysesResponse, practiceResponse] = await Promise.all([
        getAnalyses().catch(err => {
          console.error('Error fetching analyses:', err);
          return { analyses: [] };
        }),
        getPracticeSessions().catch(err => {
          console.error('Error fetching practice sessions:', err);
          return { sessions: [] };
        })
      ]);
      
      setAnalyses(analysesResponse.analyses || []);
      setPracticeSessions(practiceResponse.sessions || []);
    } catch (err) {
      console.error('Error fetching history:', err);
      setError('Failed to load your history. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewAnalysis = (analysisId) => {
    navigate(`/analysis/${analysisId}`);
  };

  const handleViewPracticeSession = (sessionId) => {
    navigate(`/practice-analysis/${sessionId}`);
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
        <button onClick={fetchAllHistory} className="btn-retry">Try Again</button>
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
        <h1>History</h1>
        <p className="subtitle">View and manage your past speech analyses and practice sessions</p>
      </div>

      {/* Tab Navigation */}
      <div className="history-tabs">
        <button
          className={`tab-button ${activeTab === 'analyses' ? 'active' : ''}`}
          onClick={() => setActiveTab('analyses')}
        >
          📊 Video Analyses ({analyses.length})
        </button>
        <button
          className={`tab-button ${activeTab === 'practice' ? 'active' : ''}`}
          onClick={() => setActiveTab('practice')}
        >
          💬 Practice Sessions ({practiceSessions.length})
        </button>
      </div>

      {activeTab === 'analyses' && (
        <>
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
        </>
      )}

      {activeTab === 'practice' && (
        <>
          {practiceSessions.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">💬</div>
              <h2>No practice sessions yet</h2>
              <p>Start a practice conversation to see your progress here!</p>
              <button 
                onClick={() => navigate('/practice')} 
                className="btn-primary"
              >
                Start Practice
              </button>
            </div>
          ) : (
            <div className="analyses-grid">
              {practiceSessions.map((session) => (
                <div 
                  key={session.id} 
                  className="analysis-card practice-card"
                  onClick={() => handleViewPracticeSession(session.id)}
                  style={{ cursor: 'pointer' }}
                >
                  <div className="card-header">
                    <h3 className="card-title">
                      Practice Session #{session.id}
                    </h3>
                    <span className="card-date">{formatDate(session.created_at)}</span>
                  </div>
                  
                  <div className="card-metrics">
                    <div className="metric">
                      <span className="metric-label">Duration</span>
                      <span className="metric-value">{formatDuration(session.duration)}</span>
                    </div>
                    <div className="metric">
                      <span className="metric-label">Flow Score</span>
                      <span className="metric-value">
                        {session.conversational_flow_score ? `${session.conversational_flow_score.toFixed(0)}/100` : 'N/A'}
                      </span>
                    </div>
                    <div className="metric">
                      <span className="metric-label">Filler Words</span>
                      <span className="metric-value">
                        {session.filler_word_count || 0}
                      </span>
                    </div>
                    <div className="metric">
                      <span className="metric-label">Engagement</span>
                      <span className="metric-value emotion-badge">
                        {session.engagement_level || 'N/A'}
                      </span>
                    </div>
                  </div>

                  {session.summary && (
                    <div className="card-summary">
                      <p>{session.summary.substring(0, 150)}{session.summary.length > 150 ? '...' : ''}</p>
                    </div>
                  )}

                  {session.key_strengths && session.key_strengths.length > 0 && (
                    <div className="card-summary" style={{ marginTop: '0.5rem', paddingTop: '0.5rem', borderTop: '1px solid #e0e0e0' }}>
                      <strong>Strengths:</strong> {session.key_strengths.slice(0, 2).join(', ')}
                    </div>
                  )}

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleViewPracticeSession(session.id);
                    }}
                    className="btn-view-analysis"
                    style={{ marginTop: '1rem' }}
                  >
                    View Full Analysis →
                  </button>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default History;
