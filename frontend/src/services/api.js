/**
 * API Service for SpeechLabs
 * Handles all communication with the backend API
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

/**
 * Upload a video file for analysis
 */
export const uploadVideo = async (formData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to upload video');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error uploading video:', error);
    throw error;
  }
};

/**
 * Send a chat message to the AI coach
 */
export const sendChatMessage = async (data) => {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to send message');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error sending chat message:', error);
    throw error;
  }
};

/**
 * Generate audio narration of Gemini analysis
 * @param {Object} geminiAnalysis - The Gemini analysis object
 * @param {string} section - Optional section to generate audio for: 'summary', 'strengths', 'improvements', 'tips', or 'all' (default)
 */
export const generateAnalysisAudio = async (geminiAnalysis, section = 'all') => {
  try {
    const response = await fetch(`${API_BASE_URL}/generate-analysis-audio`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        gemini_analysis: geminiAnalysis,
        section: section
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to generate audio');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error generating analysis audio:', error);
    throw error;
  }
};

/**
 * Check API server health
 */
export const checkApiHealth = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/healthcheck`);
    return response.ok;
  } catch (error) {
    console.error('API health check failed:', error);
    return false;
  }
};
