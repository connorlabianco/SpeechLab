import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import FeatureList from '../components/FeatureList';
import '../styles/pages/HomeLanding.css';

function HomeLanding() {
  const [showFeatures, setShowFeatures] = useState(false);
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // Prevent scrolling when home landing page is active
    document.documentElement.classList.add('home-landing-page-active');
    document.body.classList.add('home-landing-page-active');
    document.body.style.overflow = 'hidden';
    document.documentElement.style.overflow = 'hidden';
    
    return () => {
      document.documentElement.classList.remove('home-landing-page-active');
      document.body.classList.remove('home-landing-page-active');
      document.body.style.overflow = '';
      document.documentElement.style.overflow = '';
    };
  }, []);

  const handleGetStarted = () => {
    if (isAuthenticated) {
      navigate('/dashboard');
    } else {
      navigate('/login');
    }
  };

  const handleScrollDown = () => {
    setShowFeatures(true);
  };

  const handleScrollUp = () => {
    setShowFeatures(false);
  };

  return (
    <div className="home-landing-page">
      {/* Base44 gradient background elements */}
      <div className="gradient-bg"></div>
      <div className="gradient-overlay"></div>
      <div className="orb orb1"></div>
      <div className="orb orb2"></div>
      <div className="orb orb3"></div>
      <div className="orb orb4"></div>
      <div className="grain"></div>

      <div className={`home-landing-container ${showFeatures ? 'show-features' : ''}`}>
        {/* Hero Section */}
        <section className="landing-hero">
          <div className="hero-content">
            <h1>SpeechLabs</h1>
            <p className="hero-subtitle">
              Creating confidence through user-driven feedback.
            </p>
            <p className="hero-description">
              Advanced speech analysis powered by AI - at no cost. Perfect for public speaking, presentations, interviews, or confidence-building exercises.
            </p>
            <button className="btn-primary get-started-btn" onClick={handleGetStarted}>
              Get Started!
            </button>
            
            {!showFeatures && (
              <button className="scroll-indicator scroll-down" onClick={handleScrollDown}>
                <span className="arrow">▼</span>
                <span className="arrow">▼</span>
                <span className="arrow">▼</span>
              </button>
            )}
          </div>
        </section>

        {/* Key Features Section */}
        <section className="features-section">
          {showFeatures && (
            <button className="scroll-indicator scroll-up" onClick={handleScrollUp}>
              <span className="arrow">▲</span>
              <span className="arrow">▲</span>
              <span className="arrow">▲</span>
            </button>
          )}
          <div className="features-content">
            <h2>Key Features</h2>
            <FeatureList />
          </div>
        </section>
      </div>
    </div>
  );
}

export default HomeLanding;
