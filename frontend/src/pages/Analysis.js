import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getAnalysisById } from '../services/api';
import EmotionTimeline from '../components/EmotionTimeline';
import TranscriptView from '../components/TranscriptView';
import InsightPanel from '../components/InsightPanel';
import CoachChat from '../components/CoachChat';
import TabPanel from '../components/layout/TabPanel';
import '../styles/pages/Analysis.css';

function Analysis({ analysisData: propAnalysisData }) {
  const [activeTab, setActiveTab] = useState(0);
  const [analysisData, setAnalysisData] = useState(propAnalysisData);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const { id } = useParams();

  useEffect(() => {
    // If we have an ID in the URL, fetch the analysis from the database
    if (id) {
      fetchAnalysisById(id);
    } else if (propAnalysisData) {
      // If we have prop data (from new upload), use it
      setAnalysisData(propAnalysisData);
    } else {
      // No ID and no prop data, redirect to home
      navigate('/');
    }
  }, [id, propAnalysisData, navigate]);

  const fetchAnalysisById = async (analysisId) => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await getAnalysisById(analysisId);
      setAnalysisData(data);
    } catch (err) {
      console.error('Error fetching analysis:', err);
      setError('Failed to load analysis. Please try again.');
      // Redirect to history after a delay
      setTimeout(() => navigate('/history'), 2000);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <div className="loading">Loading analysis...</div>;
  }

  if (error) {
    return (
      <div className="analysis-page">
        <div className="error-message">{error}</div>
      </div>
    );
  }

  if (!analysisData) {
    return <div className="loading">Loading...</div>;
  }

  const handleTabChange = (newValue) => {
    setActiveTab(newValue);
  };

  const tabs = [
    { label: "📊 Analysis", icon: "chart-bar" },
    { label: "🧠 Insights", icon: "brain" },
    { label: "💬 AI Coach", icon: "message" }
  ];

  return (
    <div className="analysis-page">
      <h1>Speech Analysis Results</h1>
      
      <TabPanel 
        tabs={tabs} 
        activeTab={activeTab} 
        onChange={handleTabChange}
      >
        {activeTab === 0 && (
          <div className="analysis-tab">
            <div className="analysis-grid">
              <div className="analysis-section timeline-section">
                <h2>Speaking Rate Timeline</h2>
                <EmotionTimeline 
                  wpsData={analysisData.wps_data}
                />
              </div>

              <div className="analysis-section transcript-section">
                <h2>Transcript</h2>
                <TranscriptView 
                  transcriptionData={analysisData.transcription_data}
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === 1 && (
          <div className="insights-tab">
            <InsightPanel 
              geminiAnalysis={analysisData.gemini_analysis}
              emotionMetrics={analysisData.emotion_metrics}
              speechClarity={analysisData.speech_clarity}
            />
          </div>
        )}

        {activeTab === 2 && (
          <div className="coach-tab">
            <CoachChat emotionSegments={analysisData.emotion_segments} />
          </div>
        )}
      </TabPanel>
    </div>
  );
}

export default Analysis;
