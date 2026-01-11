import { createClient, AgentEvents } from '@deepgram/sdk';

const DEEPGRAM_API_KEY = process.env.REACT_APP_DEEPGRAM_API_KEY || '8c09f92cd4d1b3f8314f7d4c219cd447c39a0ec4';

export class VoiceAgentService {
  constructor() {
    this.client = null;
    this.connection = null;
    this.mediaRecorder = null;
    this.audioContext = null;
    this.mediaStream = null;
    this.audioProcessor = null;
    this.isActive = false;
  }

  async start(analysisData, onTranscript, onAgentSpeaking, onError) {
    try {
      // Create system prompt with full analysis
      const systemPrompt = this.buildSystemPrompt(analysisData);
      
      console.log('System prompt length:', systemPrompt.length);
      
      if (systemPrompt.length > 25000) {
        throw new Error('Analysis data too large for voice agent');
      }

      // Initialize Deepgram client
      this.client = createClient(DEEPGRAM_API_KEY);

      // Create voice agent connection using agent() method
      this.connection = this.client.agent();

      // Track configuration state
      let configurationComplete = false;
      
      // Promise to wait for connection to open
      const connectionOpened = new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('Connection timeout - failed to open within 10 seconds'));
        }, 10000);

        this.connection.on(AgentEvents.Open, () => {
          clearTimeout(timeout);
          console.log('Voice agent connected');
          this.isActive = true;
          
          // Send system prompt to initialize agent
          try {
            this.connection.configure({
              type: 'Settings',
              audio: {
                input: {
                  encoding: 'linear16',
                  sample_rate: 24000
                },
                output: {
                  encoding: 'linear16',
                  sample_rate: 24000,
                  container: 'none'
                }
              },
              agent: {
                language: 'en',
                listen: {
                  provider: {
                    type: 'deepgram',
                    model: 'nova-3'
                  }
                },
                think: {
                  provider: {
                    type: 'open_ai',
                    model: 'gpt-4o-mini'
                  },
                  prompt: systemPrompt
                },
                speak: {
                  provider: {
                    type: 'deepgram',
                    model: 'aura-2-thalia-en'
                  }
                },
                greeting: 'Hello! I can see your speech analysis data. What would you like to know?'
              }
            });
            console.log('Agent configured successfully');
            configurationComplete = true;
            resolve();
          } catch (configError) {
            console.error('Error configuring agent:', configError);
            reject(configError);
          }
        });

        this.connection.on(AgentEvents.Error, (error) => {
          // Only treat as critical error if configuration hasn't completed
          if (!configurationComplete) {
            clearTimeout(timeout);
            console.error('Voice agent connection error:', error);
            reject(error);
          } else {
            // After configuration, log as warning but don't break functionality
            // The Buffer error is a known SDK issue in browser environments
            if (error.code !== 'INVALID_SETTINGS' && !error.description?.includes('Buffer')) {
              console.warn('Voice agent warning (non-critical):', error);
            }
          }
        });
      });

      // Handle conversation text (both user and agent)
      this.connection.on(AgentEvents.ConversationText, (message) => {
        if (message) {
          const role = message.role || message.sender;
          const content = message.content || message.text || message.message;
          
          if (content) {
            if (role === 'user' || !role) {
              // Only log user messages in development
              if (process.env.NODE_ENV === 'development') {
                console.log('User said:', content);
              }
              onTranscript(content);
            } else if (role === 'agent' || role === 'assistant') {
              // Only log agent messages in development
              if (process.env.NODE_ENV === 'development') {
                console.log('Agent said:', content);
              }
              // Optionally add agent text to chat
            }
          }
        }
      });

      // Handle agent audio
      this.connection.on(AgentEvents.Audio, (audioData) => {
        // Agent is speaking - play audio
        if (audioData) {
          let audio;
          
          // Handle different audio data formats
          if (audioData instanceof ArrayBuffer) {
            audio = new Uint8Array(audioData);
          } else if (audioData instanceof Uint8Array) {
            audio = audioData;
          } else if (audioData instanceof Buffer) {
            // Node.js Buffer (shouldn't happen in browser, but handle it)
            audio = new Uint8Array(audioData);
          } else if (typeof audioData === 'string') {
            // If it's base64, decode it
            try {
              const binaryString = atob(audioData);
              audio = new Uint8Array(binaryString.length);
              for (let i = 0; i < binaryString.length; i++) {
                audio[i] = binaryString.charCodeAt(i);
              }
            } catch (e) {
              console.error('Error decoding audio data:', e);
              return;
            }
          } else {
            console.error('Unexpected audio data type:', typeof audioData, audioData);
            return;
          }
          
          if (audio && audio.length > 0) {
            onAgentSpeaking(audio);
          }
        }
      });

      // Error handler for post-configuration errors (non-critical)
      // Critical errors are handled in the connectionOpened promise above
      this.connection.on(AgentEvents.Error, (error) => {
        // Suppress Buffer errors and INVALID_SETTINGS errors that occur after successful config
        // These are known SDK issues in browser environments and don't affect functionality
        if (configurationComplete) {
          // Silently ignore these known non-critical errors
          if (error.code === 'INVALID_SETTINGS' || error.description?.includes('Buffer')) {
            return;
          }
          // Only log truly unexpected errors
          console.warn('Voice agent warning (non-critical):', error);
        }
      });

      this.connection.on(AgentEvents.Close, () => {
        console.log('Voice agent disconnected');
        this.isActive = false;
      });

      // Wait for connection to open before starting microphone
      await connectionOpened;
      console.log('Connection opened, starting microphone...');

      // Start microphone after connection is ready
      await this.startMicrophone();
      console.log('Microphone started, ready to send audio');

    } catch (error) {
      console.error('Failed to start voice agent:', error);
      onError(error);
      throw error;
    }
  }

  async startMicrophone() {
    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          channelCount: 1,
          sampleRate: 24000,
          echoCancellation: true,
          noiseSuppression: true
        } 
      });

      // Create audio context for processing
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 24000
      });

      // Load AudioWorklet processor
      try {
        await this.audioContext.audioWorklet.addModule('/audio-processor.js');
      } catch (error) {
        console.error('Failed to load AudioWorklet processor:', error);
        throw new Error('AudioWorklet not supported. Please use a modern browser.');
      }

      const source = this.audioContext.createMediaStreamSource(this.mediaStream);
      
      // Create AudioWorkletNode instead of ScriptProcessorNode
      this.audioProcessor = new AudioWorkletNode(this.audioContext, 'audio-processor', {
        numberOfInputs: 1,
        numberOfOutputs: 0, // We don't need output, just processing
        channelCount: 1
      });

      // Handle audio data from the worklet
      let audioChunkCount = 0;
      this.audioProcessor.port.onmessage = (event) => {
        if (!this.isActive || !this.connection) {
          if (audioChunkCount % 100 === 0) { // Log every 100 chunks to avoid spam
            console.log('Skipping audio - not active or no connection');
          }
          return;
        }

        if (event.data.type === 'audioData') {
          try {
            // Check if connection has a send method
            if (typeof this.connection.send === 'function') {
              // Send to Deepgram
              this.connection.send(event.data.data);
              audioChunkCount++;
              // Only log every 1000 chunks to reduce console spam
              if (audioChunkCount === 1 || audioChunkCount % 1000 === 0) {
                console.log(`Sent audio chunk ${audioChunkCount} to Deepgram`);
              }
            } else {
              console.warn('Connection.send is not a function. Connection type:', typeof this.connection);
              console.warn('Connection methods:', Object.keys(this.connection || {}));
            }
          } catch (error) {
            console.error('Error sending audio data:', error);
          }
        }
      };

      source.connect(this.audioProcessor);

    } catch (error) {
      console.error('Microphone access failed:', error);
      throw error;
    }
  }

  stop() {
    // Set inactive first to prevent any new operations
    this.isActive = false;

    // Stop microphone stream
    if (this.mediaStream) {
      try {
        this.mediaStream.getTracks().forEach(track => {
          if (track && typeof track.stop === 'function') {
            track.stop();
          }
        });
      } catch (error) {
        console.error('Error stopping media stream tracks:', error);
      }
      this.mediaStream = null;
    }

    // Disconnect audio processor
    if (this.audioProcessor) {
      try {
        // Send stop message to AudioWorklet
        if (this.audioProcessor.port && typeof this.audioProcessor.port.postMessage === 'function') {
          this.audioProcessor.port.postMessage('stop');
        }
        if (this.audioProcessor.disconnect && typeof this.audioProcessor.disconnect === 'function') {
          this.audioProcessor.disconnect();
        }
      } catch (error) {
        console.error('Error disconnecting audio processor:', error);
      }
      this.audioProcessor = null;
    }

    // Close Deepgram connection - be very defensive
    if (this.connection) {
      const connection = this.connection;
      this.connection = null; // Set to null first to prevent re-entry
      
      try {
        // Only try to close if connection is a valid object
        if (connection && typeof connection === 'object') {
          // Try finish() method
          if (typeof connection.finish === 'function') {
            connection.finish();
          }
          // Try close() method
          else if (typeof connection.close === 'function') {
            connection.close();
          }
          // Try sending CloseStream message
          else if (typeof connection.send === 'function') {
            try {
              connection.send(JSON.stringify({ type: 'CloseStream' }));
            } catch (e) {
              // Ignore - connection might not accept JSON
            }
          }
        }
      } catch (error) {
        // Silently handle - connection might already be closed or invalid
        // Don't log errors as this is expected in some cases
      }
    }

    // Close audio context
    if (this.audioContext) {
      try {
        if (this.audioContext.close && typeof this.audioContext.close === 'function') {
          this.audioContext.close();
        }
      } catch (error) {
        console.error('Error closing audio context:', error);
      }
      this.audioContext = null;
    }
  }

  buildSystemPrompt(analysisData) {
    const {
      duration,
      emotion_segments = [],
      transcription_data = [],
      gemini_analysis = {},
      emotion_metrics = {},
      speech_clarity = {},
      wps_data = []
    } = analysisData;

    const formatTime = (seconds) => {
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    let prompt = `# Role
You are an expert speech coach helping someone improve their public speaking. You just analyzed their speech and now you're having a live voice conversation with them to provide personalized coaching.

# General Guidelines
- Be warm, encouraging, and supportive—but also honest about areas to improve
- Speak clearly and naturally in plain language
- Keep responses to 1-2 sentences (under 120 characters) unless they ask for details (max: 300 characters)
- Do not use markdown formatting like code blocks, quotes, bold, links, or italics
- Use line breaks in lists
- Use varied phrasing; avoid repetition
- If unclear what they're asking, ask for clarification
- If asked about your well-being, respond briefly and kindly

# Voice-Specific Instructions
- Speak conversationally—your responses will be spoken aloud
- Pause after questions to allow for replies
- Confirm what they said if uncertain
- Never interrupt
- Reference specific moments using simple time references like "around the two minute mark" not exact timestamps

# Style
- Use active listening cues like "I noticed" or "I saw that"
- Be warm and understanding, but concise
- Use simple words unless they use technical terms
- Celebrate their strengths before discussing improvements

# Conversation Flow
- Start by asking what they'd like to know about their speech
- Your primary goal is to help them understand their performance and improve
- This may include:
  - Specific feedback on pacing, emotions, or clarity
  - Tips for particular moments in their speech
  - Exercises to practice
  - Explanations of their metrics
  - Encouragement and next steps

# Their Speech Data
Here's what you know about their performance:

METRICS:
- Duration: ${duration ? duration.toFixed(1) : 'N/A'} seconds
- Speaking Rate: ${speech_clarity.avg_wps ? speech_clarity.avg_wps.toFixed(1) : 'N/A'} words per second (optimal: 2 to 3)
- Clarity: ${speech_clarity.clarity_score ? speech_clarity.clarity_score.toFixed(0) : 'N/A'}%
- Main Emotion: ${emotion_metrics.main_emotion || 'N/A'}
- Emotional Range: ${emotion_metrics.emotion_diversity || 'N/A'} different emotions

`;

    // Add condensed emotion timeline
    if (emotion_segments.length > 0) {
      prompt += `EMOTION PATTERN:\n`;
      emotion_segments.slice(0, 15).forEach(seg => {
        prompt += `${seg.time_range}: ${seg.emotion}\n`;
      });
      if (emotion_segments.length > 15) {
        prompt += `(and ${emotion_segments.length - 15} more segments)\n`;
      }
      prompt += '\n';
    }

    // Add key transcript moments
    if (transcription_data.length > 0) {
      prompt += `KEY MOMENTS FROM TRANSCRIPT:\n`;
      // Include segments that are too fast, too slow, or have interesting content
      const keyMoments = transcription_data.filter(seg => 
        seg.wps > 3.0 || seg.wps < 2.0 || seg.text.length > 50
      ).slice(0, 10);
      
      keyMoments.forEach(seg => {
        const speedNote = seg.wps > 3.0 ? 'too fast' : seg.wps < 2.0 ? 'too slow' : 'good pace';
        prompt += `At ${formatTime(seg.start)}: ${seg.wps.toFixed(1)} WPS (${speedNote}), ${seg.emotion} - "${seg.text.substring(0, 80)}${seg.text.length > 80 ? '...' : ''}"\n`;
      });
      prompt += '\n';
    }

    // Add professional analysis summary
    if (gemini_analysis.summary) {
      prompt += `PROFESSIONAL ANALYSIS:\n${gemini_analysis.summary}\n\n`;
      
      if (gemini_analysis.strengths && gemini_analysis.strengths.length > 0) {
        prompt += `Strengths: ${gemini_analysis.strengths.slice(0, 3).join('. ')}\n\n`;
      }
      
      if (gemini_analysis.improvement_areas && gemini_analysis.improvement_areas.length > 0) {
        prompt += `Areas to Improve: ${gemini_analysis.improvement_areas.slice(0, 3).join('. ')}\n\n`;
      }
    }

    prompt += `# How to Reference Their Speech
- Use natural time references: "around one minute in" not "at 1:23"
- Cite specific phrases they said when relevant
- Connect feedback to exact moments: "When you said [quote], you were speaking at [X] words per second"
- Point out patterns: "I noticed your pace picked up whenever you talked about [topic]"

# Off-Scope Questions
If they ask about things outside speech coaching (health issues, unrelated topics):
"I'm focused on speech coaching, but I'm happy to help with anything related to your presentation skills"

# Conversation Opening
Start with: "Hi! I've reviewed your speech. What would you like to know about your performance?"

# Closing
When they seem satisfied, ask: "Is there anything else about your speech you'd like to work on?"
Then: "Great work today! Keep practicing and you'll see real improvement. Talk soon!"

Remember: Be conversational, specific, and encouraging. Reference their actual performance data when giving feedback.`;

    return prompt;
  }
}
