import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import VideoUploader from '../components/VideoUploader';
import ImprovementTimeline from '../components/ImprovementTimeline';
import '../styles/pages/Home.css';

function Home({ onAnalysisComplete }) {
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleUploadSuccess = (data) => {
    setIsLoading(false);
    onAnalysisComplete(data);
    // Navigate to the analysis page using the ID from the database
    if (data.analysis_id) {
      navigate(`/analysis/${data.analysis_id}`);
    } else {
      // Fallback to the old route if no ID is provided
      navigate('/analysis');
    }
  };

  const handleUploadStart = () => {
    setIsLoading(true);
  };

  const handleUploadError = (error) => {
    setIsLoading(false);
    console.error("Upload error:", error);
  };

  const handlePracticeConversationClick = () => {
    navigate('/practice');
  };

  return (
    <div className="home-page">
      <div className="home-container">
        <section className="improvement-section">
          <ImprovementTimeline />
        </section>
        
        <section className="upload-section">
          <div className="upload-card">
            <h2>Start New Analysis</h2>
            <p className="upload-subtitle">
              Upload a video of yourself speaking to get personalized feedback on your speech emotion and delivery.
            </p>
            
            <VideoUploader 
              onUploadStart={handleUploadStart}
              onUploadSuccess={handleUploadSuccess}
              onUploadError={handleUploadError}
              isLoading={isLoading}
            />
          </div>
          
          <div className="or-divider">
            <span>OR</span>
          </div>
          
          <button 
            className="conversation-practice-btn"
            onClick={handlePracticeConversationClick}
          >
            Conversation Practice
          </button>
        </section>
      </div>
    </div>
  );
}

export default Home;
