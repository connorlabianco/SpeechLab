import React, { useState, useRef, useEffect } from 'react';
import { sendChatMessage } from '../services/api';
import { VoiceAgentService } from '../services/voiceAgent';
import Card from './layout/Card';
import '../styles/components/CoachChat.css';

function CoachChat({ emotionSegments, analysisData }) {
  const [chatHistory, setChatHistory] = useState([
    { role: 'ai', content: "👋 I'm your AI speech coach. Choose text or voice mode to get started!" }
  ]);
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [isVoiceMode, setIsVoiceMode] = useState(false);
  const [isVoiceActive, setIsVoiceActive] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState('Ready');
  const [audioResponseEnabled, setAudioResponseEnabled] = useState(false);
  
  const chatEndRef = useRef(null);
  const chatMessagesRef = useRef(null);
  const audioRef = useRef(null);
  const voiceAgentRef = useRef(null);
  const audioContextRef = useRef(null);
  const audioQueueRef = useRef([]);
  const isPlayingRef = useRef(false);
  const nextPlayTimeRef = useRef(0);
  const currentAudioRef = useRef(null);
  
  // Auto-scroll chat messages container (not the entire page)
  useEffect(() => {
    if (chatMessagesRef.current && chatEndRef.current) {
      // Only scroll the chat messages container, not the page
      chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
    }
  }, [chatHistory]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (voiceAgentRef.current) {
        voiceAgentRef.current.stop();
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      // Stop any playing audio
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      }
    };
  }, []);
  
  // TEXT MODE - existing functionality
  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!message.trim()) return;
    
    const userMessage = { role: 'user', content: message };
    setChatHistory(prev => [...prev, userMessage]);
    setMessage('');
    setIsLoading(true);
    
    try {
      const response = await sendChatMessage({
        message,
        emotion_segments: emotionSegments,
        include_audio: audioResponseEnabled
      });
      
      const aiMessage = { role: 'ai', content: response.response };
      setChatHistory(prev => [...prev, aiMessage]);
      
      if (audioResponseEnabled && response.audio_url) {
        // Stop any currently playing audio
        if (currentAudioRef.current) {
          currentAudioRef.current.pause();
          currentAudioRef.current.currentTime = 0;
          currentAudioRef.current = null;
        }
        
        // Play audio automatically without showing controls
        const audio = new Audio(response.audio_url);
        currentAudioRef.current = audio;
        
        // Clean up when audio finishes
        audio.onended = () => {
          currentAudioRef.current = null;
        };
        
        audio.onerror = () => {
          currentAudioRef.current = null;
        };
        
        audio.play().catch(err => {
          console.error('Audio playback failed:', err);
          currentAudioRef.current = null;
        });
        // Don't set audioUrl state to avoid showing playback bar
      } else {
        // Clear any previous audio URL
        setAudioUrl(null);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = { 
        role: 'ai', 
        content: "I'm having trouble connecting right now. Please try again later.",
        isError: true
      };
      setChatHistory(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // VOICE MODE - Deepgram Voice Agent
  const startVoiceAgent = async () => {
    try {
      setVoiceStatus('Connecting...');
      
      // Create audio context for playback
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 24000
      });
      
      // Reset playback timing
      nextPlayTimeRef.current = 0;

      // Initialize voice agent
      voiceAgentRef.current = new VoiceAgentService();
      
      await voiceAgentRef.current.start(
        analysisData,
        
        // On user transcript
        (transcript) => {
          const userMessage = { role: 'user', content: transcript };
          setChatHistory(prev => [...prev, userMessage]);
        },
        
        // On agent speaking (audio data)
        (audioData) => {
          playAudioChunk(audioData);
        },
        
        // On agent text (to show in chat)
        (agentText) => {
          const aiMessage = { role: 'ai', content: agentText };
          setChatHistory(prev => [...prev, aiMessage]);
        },
        
        // On error
        (error) => {
          console.error('Voice agent error:', error);
          setVoiceStatus('Error - please restart');
          const errorMessage = {
            role: 'ai',
            content: 'Voice connection error. Please try again.',
            isError: true
          };
          setChatHistory(prev => [...prev, errorMessage]);
        }
      );
      
      setIsVoiceActive(true);
      setVoiceStatus('Listening... speak now');
      
      // Add initial greeting to chat
      const greeting = {
        role: 'ai',
        content: 'Voice mode active! I can see all your speech analysis data. What would you like to know?'
      };
      setChatHistory(prev => [...prev, greeting]);
      
    } catch (error) {
      console.error('Failed to start voice agent:', error);
      setVoiceStatus('Failed to connect');
      alert('Could not start voice mode. Please check microphone permissions.');
    }
  };

  const stopVoiceAgent = () => {
    if (voiceAgentRef.current) {
      voiceAgentRef.current.stop();
      voiceAgentRef.current = null;
    }
    
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    // Reset playback timing
    nextPlayTimeRef.current = 0;
    
    setIsVoiceActive(false);
    setVoiceStatus('Ready');
  };

  const playAudioChunk = (audioData) => {
    if (!audioContextRef.current) return;

    try {
      // Ensure audioData is a Uint8Array
      let audioBytes;
      if (audioData instanceof ArrayBuffer) {
        audioBytes = new Uint8Array(audioData);
      } else if (audioData instanceof Uint8Array) {
        audioBytes = audioData;
      } else {
        console.error('Unexpected audio data type:', typeof audioData);
        return;
      }

      // Check if we have valid audio data (must be multiple of 2 for 16-bit samples)
      if (audioBytes.length < 2 || audioBytes.length % 2 !== 0) {
        console.warn('Invalid audio chunk size:', audioBytes.length);
        return;
      }

      // Convert bytes to int16 samples (linear16 PCM, little-endian)
      const sampleCount = audioBytes.length / 2;
      const audioBuffer = audioContextRef.current.createBuffer(1, sampleCount, 24000);
      const channelData = audioBuffer.getChannelData(0);
      
      // Read int16 samples from bytes (little-endian)
      const dataView = new DataView(audioBytes.buffer, audioBytes.byteOffset, audioBytes.length);
      for (let i = 0; i < sampleCount; i++) {
        // Read 16-bit signed integer (little-endian)
        const int16Sample = dataView.getInt16(i * 2, true);
        // Convert to float32 range [-1.0, 1.0]
        channelData[i] = int16Sample / 32768.0;
      }
      
      // Schedule playback to start at the next available time for seamless playback
      const currentTime = audioContextRef.current.currentTime;
      const startTime = Math.max(currentTime, nextPlayTimeRef.current);
      const duration = audioBuffer.duration;
      
      const source = audioContextRef.current.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContextRef.current.destination);
      source.start(startTime);
      
      // Update next play time to ensure no gaps
      nextPlayTimeRef.current = startTime + duration;
      
    } catch (error) {
      console.error('Audio playback error:', error);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e);
    }
  };
  
  const resetChat = () => {
    if (isVoiceActive) {
      stopVoiceAgent();
    }
    
    // Stop any playing audio
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current.currentTime = 0;
      currentAudioRef.current = null;
    }
    
    setChatHistory([
      { role: 'ai', content: "👋 I'm your AI speech coach. Choose text or voice mode to get started!" }
    ]);
    setAudioUrl(null);
    // Don't reset audioResponseEnabled - let user keep their preference
  };

  const handleModeChange = (voiceMode) => {
    if (isVoiceActive) {
      stopVoiceAgent();
    }
    
    // Stop any playing audio when switching modes
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current.currentTime = 0;
      currentAudioRef.current = null;
    }
    
    // Clear chat when switching modes
    setChatHistory([
      { role: 'ai', content: "👋 I'm your AI speech coach. Choose text or voice mode to get started!" }
    ]);
    setAudioUrl(null);
    
    setIsVoiceMode(voiceMode);
  };
  
  const suggestedQuestions = [
    "How can I improve my speaking pace?",
    "What should I do to sound more confident?",
    "How can I better control my emotions while speaking?",
    "What vocal exercises would help me?",
    "How can I eliminate filler words?"
  ];
  
  const handleSuggestedQuestion = (question) => {
    if (isVoiceMode) {
      // Can't use suggested questions in voice mode
      return;
    }
    setMessage(question);
  };
  
  return (
    <Card className="coach-chat-card">
      <div className="chat-container">
        <div className="chat-messages" ref={chatMessagesRef}>
          {chatHistory.map((msg, index) => (
            <div 
              key={index} 
              className={`chat-message ${msg.role === 'user' ? 'user-message' : 'ai-message'} ${msg.isError ? 'error-message' : ''}`}
            >
              {msg.role === 'ai' && <div className="ai-avatar">🧠</div>}
              <div className="message-content">{msg.content}</div>
              {msg.role === 'user' && <div className="user-avatar">👤</div>}
            </div>
          ))}
          {isLoading && (
            <div className="chat-message ai-message loading-message">
              <div className="ai-avatar">🧠</div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>
        
        {!isVoiceMode && (
          <div className="suggested-questions">
            <h4>Try asking:</h4>
            <div className="question-buttons">
              {suggestedQuestions.map((question, index) => (
                <button 
                  key={index} 
                  className="question-button"
                  onClick={() => handleSuggestedQuestion(question)}
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}
        
        <div className="chat-input-container">
          {/* Mode Toggle */}
          <div className="mode-toggle">
            <button
              type="button"
              className={`mode-button ${!isVoiceMode ? 'active' : ''}`}
              onClick={() => handleModeChange(false)}
              disabled={isVoiceActive}
            >
              ⌨️ Text
            </button>
            <button
              type="button"
              className={`mode-button ${isVoiceMode ? 'active' : ''}`}
              onClick={() => handleModeChange(true)}
              disabled={isVoiceActive}
            >
              🎤 Voice
            </button>
          </div>
          
          {/* Text Input Mode */}
          {!isVoiceMode && (
            <form onSubmit={handleSendMessage}>
              <textarea
                className="chat-input"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask your AI coach a question..."
                disabled={isLoading}
                rows={2}
              />
              <div className="chat-buttons">
                <button 
                  type="button" 
                  className="reset-button"
                  onClick={resetChat}
                >
                  Reset
                </button>
                <button
                  type="button"
                  className={`audio-toggle-button ${audioResponseEnabled ? 'active' : ''}`}
                  onClick={() => {
                    const newValue = !audioResponseEnabled;
                    setAudioResponseEnabled(newValue);
                    
                    // Stop current audio playback if disabling
                    if (!newValue && currentAudioRef.current) {
                      currentAudioRef.current.pause();
                      currentAudioRef.current.currentTime = 0;
                      currentAudioRef.current = null;
                    }
                  }}
                  title={audioResponseEnabled ? 'Disable audio responses' : 'Enable audio responses'}
                >
                  {audioResponseEnabled ? '🔊' : '🔇'} Audio
                </button>
                <button 
                  type="submit" 
                  className="send-button"
                  disabled={isLoading || !message.trim()}
                >
                  Send
                </button>
              </div>
            </form>
          )}
          
          {/* Voice Mode */}
          {isVoiceMode && (
            <div className="voice-controls">
              <div className="voice-status">
                Status: <span className={isVoiceActive ? 'active' : ''}>{voiceStatus}</span>
              </div>
              {!isVoiceActive ? (
                <button
                  type="button"
                  className="voice-start-button"
                  onClick={startVoiceAgent}
                >
                  🎤 Start Voice Conversation
                </button>
              ) : (
                <button
                  type="button"
                  className="voice-stop-button"
                  onClick={stopVoiceAgent}
                >
                  ⏹️ Stop Voice Conversation
                </button>
              )}
              <p className="voice-hint">
                {isVoiceActive 
                  ? 'Speak naturally - the coach will respond with voice' 
                  : 'Click to start a voice conversation with your coach'}
              </p>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}

export default CoachChat;
