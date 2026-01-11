import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getPracticeSessionById } from '../services/api';
import Card from '../components/layout/Card';
import '../styles/pages/Analysis.css';

function PracticeAnalysis() {
  const [activeTab, setActiveTab] = useState(0);
  const [sessionData, setSessionData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const { id } = useParams();

  useEffect(() => {
    // If we have an ID in the URL, fetch the session from the database
    if (id) {
      fetchSessionById(id);
    } else {
      // No ID, redirect to history
      navigate('/history');
    }
  }, [id, navigate]);

  const fetchSessionById = async (sessionId) => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await getPracticeSessionById(sessionId);
      setSessionData(data);
    } catch (err) {
      console.error('Error fetching practice session:', err);
      setError('Failed to load practice session. Please try again.');
      // Redirect to history after a delay
      setTimeout(() => navigate('/history'), 2000);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <div className="loading">Loading practice session...</div>;
  }

  if (error) {
    return (
      <div className="analysis-page">
        <div className="error-message">{error}</div>
      </div>
    );
  }

  if (!sessionData) {
    return <div className="loading">Loading...</div>;
  }

  const handleTabChange = (newValue) => {
    setActiveTab(newValue);
  };

  const tabs = [
    { label: "📊 Analysis", icon: "chart-bar" },
    { label: "💬 Transcript", icon: "message" }
  ];

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="analysis-page">
      {/* Base44 gradient background elements */}
      <div className="gradient-bg"></div>
      <div className="gradient-overlay"></div>
      <div className="orb orb1"></div>
      <div className="orb orb2"></div>
      <div className="orb orb3"></div>
      <div className="orb orb4"></div>
      <div className="grain"></div>

      <h1>Practice Conversation Analysis</h1>
      
      <div className="analysis-tab">
        <div className="analysis-grid">
          {/* Summary Section */}
          <div className="analysis-section" style={{ gridColumn: '1 / -1' }}>
            <h2>Summary</h2>
            <p style={{ lineHeight: '1.6', fontSize: '1.1rem' }}>{sessionData.summary}</p>
          </div>

          {/* Metrics Grid */}
          <div className="analysis-section">
            <h2>Conversation Metrics</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
              <div>
                <strong>Flow Score:</strong>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#007bff', marginTop: '0.5rem' }}>
                  {sessionData.conversational_flow_score?.toFixed(0) || 'N/A'}/100
                </div>
              </div>
              <div>
                <strong>Engagement:</strong>
                <div style={{ fontSize: '1.5rem', textTransform: 'capitalize', marginTop: '0.5rem' }}>
                  {sessionData.engagement_level || 'N/A'}
                </div>
              </div>
              <div>
                <strong>Duration:</strong>
                <div style={{ fontSize: '1.5rem', marginTop: '0.5rem' }}>
                  {formatDuration(sessionData.duration)}
                </div>
              </div>
              <div>
                <strong>Filler Words:</strong>
                <div style={{ fontSize: '1.5rem', marginTop: '0.5rem' }}>
                  {sessionData.filler_word_count || 0}
                </div>
              </div>
              <div>
                <strong>Avg Response Length:</strong>
                <div style={{ fontSize: '1.5rem', marginTop: '0.5rem' }}>
                  {sessionData.avg_response_length_words || 0} words
                </div>
              </div>
              <div>
                <strong>Topic Coherence:</strong>
                <div style={{ fontSize: '1.5rem', textTransform: 'capitalize', marginTop: '0.5rem' }}>
                  {sessionData.topic_coherence || 'N/A'}
                </div>
              </div>
            </div>
          </div>

          {/* Key Strengths */}
          {sessionData.key_strengths && sessionData.key_strengths.length > 0 && (
            <div className="analysis-section">
              <h2>✅ Key Strengths</h2>
              <ul style={{ lineHeight: '1.8', paddingLeft: '1.5rem' }}>
                {sessionData.key_strengths.map((strength, idx) => (
                  <li key={idx} style={{ marginBottom: '0.5rem' }}>{strength}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Improvement Areas */}
          {sessionData.improvement_areas && sessionData.improvement_areas.length > 0 && (
            <div className="analysis-section">
              <h2>📈 Areas for Improvement</h2>
              <ul style={{ lineHeight: '1.8', paddingLeft: '1.5rem' }}>
                {sessionData.improvement_areas.map((area, idx) => (
                  <li key={idx} style={{ marginBottom: '0.5rem' }}>{area}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Filler Words Breakdown */}
          {sessionData.filler_words_breakdown && (
            <div className="analysis-section" style={{ gridColumn: '1 / -1' }}>
              <h2>Filler Words Breakdown</h2>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '1rem' }}>
                {Object.entries(sessionData.filler_words_breakdown).map(([word, count]) => (
                  <div key={word} style={{ textAlign: 'center', padding: '0.5rem', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
                    <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>{count}</div>
                    <div style={{ fontSize: '0.9rem', color: '#666' }}>{word}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Transcript */}
          {sessionData.conversation_transcript && sessionData.conversation_transcript.length > 0 && (
            <div className="analysis-section" style={{ gridColumn: '1 / -1' }}>
              <h2>💬 Conversation Transcript</h2>
              <div style={{ maxHeight: '400px', overflowY: 'auto', padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
                {sessionData.conversation_transcript.map((msg, idx) => (
                  <div key={idx} style={{ marginBottom: '1rem', padding: '0.75rem', backgroundColor: msg.role === 'user' ? '#e3f2fd' : '#fff', borderRadius: '4px', borderLeft: `4px solid ${msg.role === 'user' ? '#2196f3' : '#4caf50'}` }}>
                    <strong style={{ color: msg.role === 'user' ? '#1976d2' : '#2e7d32' }}>
                      {msg.role === 'user' ? '👤 You' : '💬 Assistant'}:
                    </strong>
                    <p style={{ margin: '0.5rem 0 0 0', lineHeight: '1.6' }}>{msg.content}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default PracticeAnalysis;
