import React from 'react';
import Card from './layout/Card';
import '../styles/components/FeatureList.css';

function FeatureList() {
  const features = [
    {
      title: 'Video Upload',
      description: 'Upload a video of yourself speaking to get personalized feedback.'
    },
    {
      title: 'Speech Emotion Recognition',
      description: 'Detects tone, mood, and speaking style using advanced AI models.'
    },
    {
      title: 'Speaking Rate Analysis',
      description: 'Measures your words-per-second rate with optimal range indicators (2.0-3.0 WPS) and variation analysis.'
    },
    {
      title: 'AI-Powered Feedback',
      description: 'Get personalized insights and tips to improve your delivery using Google Gemini AI.'
    },
    {
      title: 'AI Speech Coach',
      description: 'Chat with an AI coach for specific advice on improving your speech patterns.'
    },
    {
      title: 'Audio Feedback',
      description: 'Listen to coaching advice with AI-generated voice feedback.'
    },
    {
      title: 'Interactive Visualizations',
      description: 'View detailed timelines of your emotion patterns and speaking rate with interactive charts.'
    }
  ];

  return (
    <div className="feature-list">
      {features.map((feature, index) => (
        <Card key={index} className="feature-card">
          <h3 className="feature-title">{feature.title}</h3>
          <p className="feature-description">{feature.description}</p>
        </Card>
      ))}
    </div>
  );
}

export default FeatureList;
