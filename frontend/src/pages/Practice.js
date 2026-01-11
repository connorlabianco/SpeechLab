import React from 'react';
import PracticeConversation from '../components/PracticeConversation';
import '../styles/pages/Practice.css';

function Practice() {
  return (
    <div className="practice-page">
      {/* Base44 gradient background elements */}
      <div className="gradient-bg"></div>
      <div className="gradient-overlay"></div>
      <div className="orb orb1"></div>
      <div className="orb orb2"></div>
      <div className="orb orb3"></div>
      <div className="orb orb4"></div>
      <div className="grain"></div>

      <div className="practice-container">
        <h1>Practice Conversation</h1>
        <p className="practice-subtitle">
          Have a natural conversation to improve your conversational awareness and speaking skills.
        </p>
        <PracticeConversation />
      </div>
    </div>
  );
}

export default Practice;
