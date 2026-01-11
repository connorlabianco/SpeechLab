import React, { useState, useRef, useEffect } from 'react';
import { VoiceAgentService } from '../services/voiceAgent';
import Card from './layout/Card';
import '../styles/components/CoachChat.css';

function PracticeConversation() {
  const [chatHistory, setChatHistory] = useState([]);
  const [isVoiceActive, setIsVoiceActive] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState('Ready');
  const [conversationEnded, setConversationEnded] = useState(false);
  
  const chatEndRef = useRef(null);
  const chatMessagesRef = useRef(null);
  const voiceAgentRef = useRef(null);
  const audioContextRef = useRef(null);
  const nextPlayTimeRef = useRef(0);
  const conversationHistoryRef = useRef([]);
  const waitingForFeedbackRef = useRef(false);
  const activeAudioSourcesRef = useRef([]);
  const isAgentSpeakingRef = useRef(false);
  
  // Auto-scroll chat messages container
  useEffect(() => {
    if (chatMessagesRef.current && chatEndRef.current) {
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
    };
  }, []);

  // Check if user wants to end conversation
  const checkForEndSignal = (transcript) => {
    const endSignals = [
      'that\'s all', 'thats all', 'i\'m done', 'im done', 'i am done',
      'let\'s end', 'lets end', 'finish', 'stop', 'end conversation',
      'wrap up', 'we\'re done', 'were done', 'all done', 'conversation over',
      'end it', 'done talking', 'finished', 'that\'s it', 'thats it'
    ];
    
    const lowerTranscript = transcript.toLowerCase().trim();
    return endSignals.some(signal => lowerTranscript.includes(signal));
  };

  const stopAllAudio = () => {
    // Stop all active audio sources
    activeAudioSourcesRef.current.forEach(source => {
      try {
        if (source && typeof source.stop === 'function') {
          source.stop();
        }
      } catch (error) {
        // Ignore errors when stopping sources
      }
    });
    activeAudioSourcesRef.current = [];
    // Reset playback timing
    nextPlayTimeRef.current = audioContextRef.current ? audioContextRef.current.currentTime : 0;
  };

  // VOICE MODE - Practice Conversation
  const startVoiceAgent = async () => {
    try {
      setVoiceStatus('Connecting...');
      setConversationEnded(false);
      conversationHistoryRef.current = [];
      
      // Create audio context for playback
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 24000
      });
      
      // Reset playback timing
      nextPlayTimeRef.current = 0;

      // Initialize voice agent in practice mode
      voiceAgentRef.current = new VoiceAgentService();
      
      await voiceAgentRef.current.start(
        null, // No analysis data needed for practice
        
        // On user transcript
        (transcript) => {
          // Stop all agent audio immediately if user is interrupting
          if (isAgentSpeakingRef.current || activeAudioSourcesRef.current.length > 0) {
            stopAllAudio();
            isAgentSpeakingRef.current = false;
          }
          
          const userMessage = { role: 'user', content: transcript };
          setChatHistory(prev => [...prev, userMessage]);
          conversationHistoryRef.current.push({ role: 'user', content: transcript });
          
          // Check if user wants to end conversation
          if (checkForEndSignal(transcript)) {
            handleConversationEnd();
          }
        },
        
        // On agent speaking (audio data)
        (audioData) => {
          isAgentSpeakingRef.current = true;
          playAudioChunk(audioData);
        },
        
        // On agent text (to show in chat)
        (agentText) => {
          const aiMessage = { role: 'ai', content: agentText };
          setChatHistory(prev => [...prev, aiMessage]);
          conversationHistoryRef.current.push({ role: 'assistant', content: agentText });
          
          // If we're waiting for feedback and this looks like feedback, stop after a delay
          if (waitingForFeedbackRef.current) {
            // Check if this response contains feedback indicators
            const feedbackKeywords = ['feedback', 'conversation', 'speaking', 'pace', 'clarity', 'awareness', 'improve', 'strength'];
            const lowerText = agentText.toLowerCase();
            const isFeedback = feedbackKeywords.some(keyword => lowerText.includes(keyword));
            
            if (isFeedback || agentText.length > 100) {
              // This is likely the feedback response, stop after it finishes
              setTimeout(() => {
                if (voiceAgentRef.current) {
                  voiceAgentRef.current.stop();
                  voiceAgentRef.current = null;
                }
                setIsVoiceActive(false);
                setVoiceStatus('Conversation ended - feedback provided above');
                waitingForFeedbackRef.current = false;
              }, 8000); // Wait 8 seconds for audio to finish
            }
          }
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
        },
        
        'practice' // Mode: practice conversation
      );
      
      setIsVoiceActive(true);
      setVoiceStatus('Listening... speak now');
      
    } catch (error) {
      console.error('Failed to start voice agent:', error);
      setVoiceStatus('Failed to connect');
      alert('Could not start voice mode. Please check microphone permissions.');
    }
  };

  const handleConversationEnd = () => {
    if (conversationEnded) return; // Prevent multiple triggers
    
    setConversationEnded(true);
    setVoiceStatus('Ending conversation - waiting for feedback...');
    waitingForFeedbackRef.current = true;
    
    // The agent will automatically provide feedback based on the prompt
    // We'll wait for the agent's response (handled in onAgentText callback)
    // If no response comes within 15 seconds, stop anyway
    setTimeout(() => {
      if (waitingForFeedbackRef.current && voiceAgentRef.current) {
        voiceAgentRef.current.stop();
        voiceAgentRef.current = null;
        setIsVoiceActive(false);
        setVoiceStatus('Conversation ended');
        waitingForFeedbackRef.current = false;
      }
    }, 15000); // Safety timeout
  };

  const stopVoiceAgent = () => {
    // Stop all audio first
    stopAllAudio();
    
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
    isAgentSpeakingRef.current = false;
    
    setIsVoiceActive(false);
    setVoiceStatus('Ready');
    setConversationEnded(false);
    waitingForFeedbackRef.current = false;
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
      
      // Track this source so we can stop it if interrupted
      activeAudioSourcesRef.current.push(source);
      
      // Remove source when it finishes playing
      source.onended = () => {
        const index = activeAudioSourcesRef.current.indexOf(source);
        if (index > -1) {
          activeAudioSourcesRef.current.splice(index, 1);
        }
        // If no more sources, agent is done speaking
        if (activeAudioSourcesRef.current.length === 0) {
          isAgentSpeakingRef.current = false;
        }
      };
      
      // Update next play time to ensure no gaps
      nextPlayTimeRef.current = startTime + duration;
      
    } catch (error) {
      console.error('Audio playback error:', error);
    }
  };
  
  const resetConversation = () => {
    if (isVoiceActive) {
      stopVoiceAgent();
    }
    
    setChatHistory([]);
    conversationHistoryRef.current = [];
    setConversationEnded(false);
    waitingForFeedbackRef.current = false;
  };

  return (
    <Card className="coach-chat-card">
      <div className="chat-container">
        <div className="chat-messages" ref={chatMessagesRef}>
          {chatHistory.length === 0 && (
            <div className="chat-message ai-message">
              <div className="ai-avatar">💬</div>
              <div className="message-content">
                Welcome to Practice Conversation! This is a safe space to practice your conversational skills. 
                When you're ready to end, just let me know and I'll share feedback on how you did.
              </div>
            </div>
          )}
          {chatHistory.map((msg, index) => (
            <div 
              key={index} 
              className={`chat-message ${msg.role === 'user' ? 'user-message' : 'ai-message'} ${msg.isError ? 'error-message' : ''} ${msg.isFeedback ? 'feedback-message' : ''}`}
            >
              {msg.role === 'ai' && <div className="ai-avatar">💬</div>}
              <div className="message-content">{msg.content}</div>
              {msg.role === 'user' && <div className="user-avatar">👤</div>}
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>
        
        <div className="chat-input-container">
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
                🎤 Start Practice Conversation
              </button>
            ) : (
              <button
                type="button"
                className="voice-stop-button"
                onClick={stopVoiceAgent}
              >
                ⏹️ End Conversation
              </button>
            )}
            <p className="voice-hint">
              {isVoiceActive 
                ? 'Speak naturally - let me know when you want to end and I\'ll share feedback' 
                : 'Click to start a practice conversation. When done, say "that\'s all" or "let\'s end" for feedback'}
            </p>
            {chatHistory.length > 0 && !isVoiceActive && (
              <button
                type="button"
                className="reset-button"
                onClick={resetConversation}
                style={{ marginTop: '0.5rem' }}
              >
                Reset Conversation
              </button>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}

export default PracticeConversation;
