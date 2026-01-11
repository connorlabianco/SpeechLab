# SpeechLabs Complete Setup Guide

## Quick Start Summary

This project has been restructured to use **Deepgram API** instead of OpenAI Whisper for better performance and cloud-based processing.

---

## What's Already Created ✓

### Backend Files (Complete)
All backend files have been created in `/home/claude/speechlabs/backend/`:

- ✓ `app.py` - Main Flask application
- ✓ `requirements.txt` - Python dependencies (includes Deepgram SDK)
- ✓ `.env.example` - Environment variables template
- ✓ `api/routes.py` - API endpoints with Deepgram integration
- ✓ `services/deepgram_service.py` - **NEW** Deepgram STT and TTS service
- ✓ `services/gemini_service.py` - Updated Gemini AI service
- ✓ `services/speech_analysis.py` - Emotion recognition
- ✓ `services/audio_service.py` - Audio segmentation
- ✓ `utils/data_processor.py` - Data processing utilities
- ✓ `utils/visualization.py` - Visualization helpers
- ✓ All `__init__.py` files

### Documentation
- ✓ `README.md` - Comprehensive project documentation
- ✓ `MIGRATION_GUIDE.md` - Migration details from Speechably

### Frontend Structure
- ✓ `frontend/package.json` - React dependencies
- ✓ Directory structure created

---

## Files to Copy from Speechably

### Priority 1: Essential Files (Copy As-Is)

#### Public Files
```
speechably/frontend/public/index.html → speechlabs/frontend/public/index.html
speechably/frontend/public/manifest.json → speechlabs/frontend/public/manifest.json
speechably/frontend/public/favicon.ico → speechlabs/frontend/public/favicon.ico
```

#### Core React Files
```
speechably/frontend/src/index.js → speechlabs/frontend/src/index.js
speechably/frontend/src/App.js → speechlabs/frontend/src/App.js
```

#### Services
```
speechably/frontend/src/services/api.js → speechlabs/frontend/src/services/api.js
```

#### Layout Components
```
speechably/frontend/src/components/layout/Card.js → speechlabs/frontend/src/components/layout/Card.js
speechably/frontend/src/components/layout/Loading.js → speechlabs/frontend/src/components/layout/Loading.js
speechably/frontend/src/components/layout/TabPanel.js → speechlabs/frontend/src/components/layout/TabPanel.js
```

#### Analysis Components
```
speechably/frontend/src/components/EmotionTimeline.js → speechlabs/frontend/src/components/EmotionTimeline.js
speechably/frontend/src/components/TranscriptView.js → speechlabs/frontend/src/components/TranscriptView.js
speechably/frontend/src/components/InsightPanel.js → speechlabs/frontend/src/components/InsightPanel.js
speechably/frontend/src/components/VideoUploader.js → speechlabs/frontend/src/components/VideoUploader.js
```

#### Pages
```
speechably/frontend/src/pages/Analysis.js → speechlabs/frontend/src/pages/Analysis.js
speechably/frontend/src/pages/NotFound.js → speechlabs/frontend/src/pages/NotFound.js
```

#### All CSS Files
```
speechably/frontend/src/styles/App.css → speechlabs/frontend/src/styles/App.css
speechably/frontend/src/styles/components/ → speechlabs/frontend/src/styles/components/ (entire directory)
speechably/frontend/src/styles/pages/ → speechlabs/frontend/src/styles/pages/ (entire directory)
```

---

## Files That Need Minor Updates

### 1. Header.js (Update Branding)
```javascript
// speechably/frontend/src/components/layout/Header.js
// Change "Speechably" to "SpeechLabs"

function Header() {
  return (
    <header className="header">
      <div className="header-container">
        <Link to="/" className="logo">
          <span className="logo-icon">🗣️</span>
          <span className="logo-text">SpeechLabs</span>  {/* CHANGED */}
        </Link>
        {/* ... rest of component ... */}
```

### 2. Footer.js (Update Branding)
```javascript
// Change copyright text
<p>&copy; {currentYear} SpeechLabs. All rights reserved.</p>  {/* CHANGED */}
```

### 3. Home.js (Update Branding)
```javascript
// Change hero section
<h1>SpeechLabs</h1>  {/* CHANGED */}
<p className="tagline">Creating confidence through user-driven feedback.</p>
```

### 4. CoachChat.js (Add Audio Playback)
Add this functionality to play Deepgram TTS audio:

```javascript
// Add state for audio
const [audioUrl, setAudioUrl] = useState(null);

// Update handleSendMessage
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
      emotion_segments: emotionSegments
    });
    
    const aiMessage = { role: 'ai', content: response.response };
    setChatHistory(prev => [...prev, aiMessage]);
    
    // NEW: Handle audio feedback
    if (response.audio_url) {
      setAudioUrl(response.audio_url);
      const audio = new Audio(response.audio_url);
      audio.play().catch(err => console.error('Audio playback failed:', err));
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

// Optionally add an audio player to the JSX (at the bottom of the component)
{audioUrl && (
  <div className="audio-feedback">
    <audio src={audioUrl} controls />
  </div>
)}
```

### 5. FeatureList.js (Update Features)
Add a new feature for Deepgram TTS:

```javascript
const features = [
  {
    icon: '🎥',
    title: 'Video Upload',
    description: 'Upload a video of yourself speaking to get personalized feedback.'
  },
  {
    icon: '🔊',
    title: 'Speech Emotion Recognition',
    description: 'Detects tone, mood, and speaking style using advanced AI models.'
  },
  {
    icon: '📊',
    title: 'Speaking Rate Analysis',
    description: 'Measures your words-per-second rate and identifies optimal pacing.'
  },
  {
    icon: '🧠',
    title: 'AI-Powered Feedback',
    description: 'Get personalized insights and tips to improve your delivery.'
  },
  {
    icon: '💬',
    title: 'AI Speech Coach',
    description: 'Chat with an AI coach for specific advice on improving your speech.'
  },
  {
    icon: '🔊',  // NEW FEATURE
    title: 'Audio Feedback',
    description: 'Listen to coaching advice with AI-generated voice feedback.'
  },
  {
    icon: '📈',
    title: 'Interactive Visualizations',
    description: 'View detailed timelines of your emotion patterns and speaking rate.'
  }
];
```

### 6. index.html (Update Title and Description)
```html
<title>SpeechLabs | Speech Analysis</title>
<meta
  name="description"
  content="SpeechLabs - AI-powered speech analysis for improving public speaking"
/>
```

---

## Installation & Setup

### Step 1: Backend Setup
```bash
cd speechlabs/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
GEMINI_API_KEY=your_gemini_api_key_here
DEEPGRAM_API_KEY=8c09f92cd4d1b3f8314f7d4c219cd447c39a0ec4
FFMPEG_PATH=ffmpeg
FLASK_ENV=development
FLASK_DEBUG=True
EOF

# Start the backend
python app.py
```

### Step 2: Frontend Setup
```bash
cd speechlabs/frontend

# Install dependencies
npm install

# Start the development server
npm start
```

### Step 3: Verify Setup
1. Backend should be running on `http://localhost:5000`
2. Frontend should open in browser at `http://localhost:3000`
3. Try uploading a test video
4. Check that Deepgram transcription is working
5. Test the AI coach chat feature
6. Verify audio feedback plays correctly

---

## File Copy Commands (Unix/Mac)

If you want to copy files programmatically:

```bash
# Navigate to parent directory containing both projects
cd /path/to/projects

# Copy public files
cp speechably/frontend/public/* speechlabs/frontend/public/

# Copy src files
cp speechably/frontend/src/index.js speechlabs/frontend/src/
cp speechably/frontend/src/App.js speechlabs/frontend/src/

# Copy services
cp -r speechably/frontend/src/services/* speechlabs/frontend/src/services/

# Copy components
cp -r speechably/frontend/src/components/* speechlabs/frontend/src/components/

# Copy pages
cp -r speechably/frontend/src/pages/* speechlabs/frontend/src/pages/

# Copy styles
cp -r speechably/frontend/src/styles/* speechlabs/frontend/src/styles/
```

Then make the manual updates listed above.

---

## Testing Checklist

- [ ] Backend starts without errors
- [ ] Frontend starts and displays homepage
- [ ] Can upload video file
- [ ] Video is processed and analyzed
- [ ] Emotion timeline displays correctly
- [ ] Transcript shows with timing information
- [ ] Insights panel shows AI feedback
- [ ] Can chat with AI coach
- [ ] Audio feedback plays when chatting
- [ ] All visualizations render properly

---

## Key Differences from Speechably

1. **No Whisper Installation Required** - Uses cloud-based Deepgram API
2. **Audio Feedback** - Coach responses now include voice audio
3. **Better Transcription** - Smart Formatting for punctuation and capitalization
4. **Faster Processing** - Cloud API is generally faster than local Whisper
5. **Scalability** - Easy to scale without local GPU requirements

---

## Deployment Notes

### Backend Deployment
- Ensure environment variables are set on server
- Use `gunicorn` for production: `gunicorn -w 4 -b 0.0.0.0:5000 app:app`
- Set up CORS properly for production domain
- Configure file upload limits

### Frontend Deployment
- Build production bundle: `npm run build`
- Serve static files or use service like Vercel/Netlify
- Update API_BASE_URL in production

---

## Support

For issues or questions:
1. Check the README.md
2. Review MIGRATION_GUIDE.md
3. Check Deepgram API status at https://status.deepgram.com/
4. Verify API keys are correct

---

## Next Steps

1. ✅ Copy all frontend files from Speechably
2. ✅ Make branding updates (Speechably → SpeechLabs)
3. ✅ Add audio playback to CoachChat
4. ✅ Test complete workflow
5. ✅ Deploy to production

Good luck with your competition! 🚀
