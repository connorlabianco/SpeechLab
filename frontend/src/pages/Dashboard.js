import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAnalyses, uploadVideo } from '../services/api';
import ImprovementTimeline from '../components/ImprovementTimeline';
import Loading from '../components/layout/Loading';
import '../styles/pages/Dashboard.css';

function Dashboard() {
  const [analyses, setAnalyses] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [filterCount, setFilterCount] = useState(10);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchAnalyses();
  }, []);

  useEffect(() => {
    // Prevent scrolling when dashboard page is active
    document.documentElement.classList.add('dashboard-page-active');
    document.body.classList.add('dashboard-page-active');
    document.body.style.overflow = 'hidden';
    document.documentElement.style.overflow = 'hidden';
    
    return () => {
      document.documentElement.classList.remove('dashboard-page-active');
      document.body.classList.remove('dashboard-page-active');
      document.body.style.overflow = '';
      document.documentElement.style.overflow = '';
    };
  }, []);

  const fetchAnalyses = async () => {
    try {
      const response = await getAnalyses();
      setAnalyses(response.analyses || []);
    } catch (error) {
      console.error('Error fetching analyses:', error);
    }
  };

  const handleFilterChange = (newCount) => {
    setFilterCount(newCount);
  };

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setIsUploading(true);
      const formData = new FormData();
      formData.append('file', file);
      const data = await uploadVideo(formData);
      if (data.analysis_id) {
        navigate(`/analysis/${data.analysis_id}`);
      } else {
        navigate('/analysis');
      }
    } catch (error) {
      setIsUploading(false);
      console.error("Upload error:", error);
      alert(error.message || 'Failed to upload video. Please try again.');
    }
  };

  const handleSpeechAnalysisClick = () => {
    fileInputRef.current?.click();
  };

  const handlePracticeConversationClick = () => {
    navigate('/practice');
  };

  // Calculate today's analyses count
  const today = new Date().toDateString();
  const todayAnalyses = analyses.filter(analysis => {
    const analysisDate = new Date(analysis.created_at).toDateString();
    return analysisDate === today;
  }).length;

  return (
    <div className="dashboard-page">
      {/* Base44 gradient background elements */}
      <div className="gradient-bg"></div>
      <div className="gradient-overlay"></div>
      <div className="orb orb1"></div>
      <div className="orb orb2"></div>
      <div className="orb orb3"></div>
      <div className="orb orb4"></div>
      <div className="grain"></div>

      <div className="dashboard-container">
        <div className="dashboard-grid">
          <div className="dashboard-card timeline-card">
            <ImprovementTimeline onFilterChange={handleFilterChange} />
          </div>

          <div className="dashboard-card usage-card">
            <h3>Daily Analysis Used</h3>
            <div className="metric-value-large">
              {todayAnalyses}/5
            </div>
            <p className="metric-description">
              Analyses remaining today
            </p>
          </div>

          <div className="dashboard-card actions-card">
            {isUploading ? (
              <Loading message="Analyzing speech patterns and emotions..." />
            ) : (
              <>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileSelect}
                  accept="video/mp4,video/x-m4v,video/*"
                  className="file-input-hidden"
                />

                <button
                  className="btn-primary speech-analysis-button"
                  onClick={handleSpeechAnalysisClick}
                >
                  Speech Analysis
                </button>

                <div className="or-divider">
                  <span>OR</span>
                </div>

                <button 
                  className="btn-primary practice-button"
                  onClick={handlePracticeConversationClick}
                >
                  Practice Conversation
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
