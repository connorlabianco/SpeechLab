/**
 * API Service for SpeechLabs
 * Handles all communication with the backend API
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

/**
 * Get current authenticated user
 */
export const getCurrentUser = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/user`, {
      method: 'GET',
      credentials: 'include'
    });
    
    if (response.status === 401) {
      return null;
    }
    
    if (!response.ok) {
      throw new Error('Failed to get user');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error getting current user:', error);
    return null;
  }
};

/**
 * Logout the current user
 */
export const logout = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/logout`, {
      method: 'POST',
      credentials: 'include'
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to logout');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error logging out:', error);
    throw error;
  }
};

/**
 * Upload a video file for analysis
 */
export const uploadVideo = async (formData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      credentials: 'include',
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
      credentials: 'include',
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
      credentials: 'include',
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
 * Get all analyses for the current user (dashboard/history)
 */
export const getAnalyses = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/dashboard`, {
      method: 'GET',
      credentials: 'include'
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to fetch analyses');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching analyses:', error);
    throw error;
  }
};

/**
 * Get a specific analysis by ID
 */
export const getAnalysisById = async (analysisId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/analysis/${analysisId}`, {
      method: 'GET',
      credentials: 'include'
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to fetch analysis');
    }
    
    const data = await response.json();
    return data.analysis;
  } catch (error) {
    console.error('Error fetching analysis:', error);
    throw error;
  }
};

/**
 * Get all practice sessions for the current user
 */
export const getPracticeSessions = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/practice-history`, {
      method: 'GET',
      credentials: 'include'
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to fetch practice sessions');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching practice sessions:', error);
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
