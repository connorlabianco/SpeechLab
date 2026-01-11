# Migration Guide: Speechably → SpeechLabs

## Overview
This document outlines the changes made when migrating from Speechably to SpeechLabs, specifically the transition from OpenAI Whisper to Deepgram API.

---

## Key Changes

### 1. **API Integration**
- **Removed**: OpenAI Whisper (local installation)
- **Added**: Deepgram SDK for both Speech-to-Text and Text-to-Speech

### 2. **New Service: deepgram_service.py**
Replaces the old `transcription.py` file with enhanced functionality:

**Features**:
- `transcribe_segments()` - Transcribes audio segments using Deepgram Nova-2 model
- `transcribe_full_audio()` - Transcribes complete audio with timestamps
- `text_to_speech()` - Converts coaching feedback to audio using Deepgram TTS
- `get_speech_metrics()` - Calculates speaking metrics
- `format_transcript_with_timestamps()` - Formats transcript for display

**Deepgram Configuration**:
```python
options = PrerecordedOptions(
    model="nova-2",
    language="en",
    smart_format=True,  # Enables Smart Formatting
    punctuate=True,
    paragraphs=True,
    utterances=True
)
```

### 3. **Updated Backend Files**

#### `backend/requirements.txt`
- **Removed**: `openai-whisper>=20231117`
- **Added**: `deepgram-sdk>=3.0.0,<4.0.0`

#### `backend/api/routes.py`
- Updated imports to use `DeepgramService` instead of `TranscriptionService`
- Added audio feedback generation in `/api/chat` endpoint:
```python
audio_url = deepgram_service.text_to_speech(response)
return jsonify({
    'response': response,
    'audio_url': audio_url  # Base64 encoded audio
})
```

#### `backend/services/gemini_service.py`
- Updated model to `gemini-2.0-flash-exp` (latest version)
- No functional changes to prompts or logic

---

## Frontend Changes Required

### 1. **Update CoachChat.js**
Add audio playback functionality for TTS responses:

```javascript
const [audioUrl, setAudioUrl] = useState(null);

const handleSendMessage = async (e) => {
  e.preventDefault();
  // ... existing code ...
  
  const response = await sendChatMessage({
    message,
    emotion_segments: emotionSegments
  });
  
  // Add AI response to chat
  const aiMessage = { role: 'ai', content: response.response };
  setChatHistory(prev => [...prev, aiMessage]);
  
  // Handle audio feedback
  if (response.audio_url) {
    setAudioUrl(response.audio_url);
    // Optionally auto-play
    const audio = new Audio(response.audio_url);
    audio.play();
  }
};
```

### 2. **All Other Frontend Files**
The following files can be copied directly from Speechably without changes:
- All files in `src/components/`
- All files in `src/pages/`
- All files in `src/styles/`
- `src/App.js`
- `src/index.js`
- `public/index.html`
- `public/manifest.json`

---

## File Structure

### Backend (Complete ✓)
```
backend/
├── api/
│   ├── __init__.py ✓
│   └── routes.py ✓
├── services/
│   ├── __init__.py ✓
│   ├── audio_service.py ✓
│   ├── deepgram_service.py ✓ (NEW)
│   ├── gemini_service.py ✓
│   └── speech_analysis.py ✓
├── utils/
│   ├── __init__.py ✓
│   ├── data_processor.py ✓
│   └── visualization.py ✓
├── __init__.py ✓
├── app.py ✓
├── requirements.txt ✓
└── .env.example ✓
```

### Frontend (Copy from Speechably)
```
frontend/
├── public/
│   ├── index.html (copy from Speechably)
│   ├── manifest.json (copy from Speechably)
│   └── favicon.ico (copy from Speechably)
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Card.js (copy)
│   │   │   ├── Footer.js (copy)
│   │   │   ├── Header.js (copy, update branding)
│   │   │   ├── Loading.js (copy)
│   │   │   └── TabPanel.js (copy)
│   │   ├── CoachChat.js (copy, add audio playback)
│   │   ├── EmotionTimeline.js (copy)
│   │   ├── FeatureList.js (copy, update feature descriptions)
│   │   ├── InsightPanel.js (copy)
│   │   ├── TranscriptView.js (copy)
│   │   └── VideoUploader.js (copy)
│   ├── pages/
│   │   ├── Analysis.js (copy)
│   │   ├── Home.js (copy, update branding)
│   │   └── NotFound.js (copy)
│   ├── services/
│   │   └── api.js (copy)
│   ├── styles/
│   │   ├── components/ (copy all)
│   │   ├── pages/ (copy all)
│   │   └── App.css (copy)
│   ├── App.js (copy)
│   └── index.js (copy)
└── package.json ✓
```

---

## Branding Updates

Update these instances of "Speechably" to "SpeechLabs":

### Files to Update:
1. `frontend/src/components/layout/Header.js`
   - Logo text
   - Page title

2. `frontend/src/components/layout/Footer.js`
   - Copyright text

3. `frontend/src/pages/Home.js`
   - Hero heading
   - Tagline

4. `frontend/src/components/FeatureList.js`
   - Add feature for "AI-powered audio feedback" using Deepgram TTS

5. `frontend/public/index.html`
   - Title tag
   - Meta description

---

## Environment Variables

Create `backend/.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
DEEPGRAM_API_KEY=8c09f92cd4d1b3f8314f7d4c219cd447c39a0ec4
FFMPEG_PATH=ffmpeg
FLASK_ENV=development
FLASK_DEBUG=True
```

---

## Setup Instructions

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file with your API keys
python app.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

---

## Testing Deepgram Integration

### Test Transcription
```python
from services.deepgram_service import DeepgramService

service = DeepgramService(api_key="your_key")
result = service.transcribe_full_audio("path/to/audio.wav")
print(result['transcript'])
```

### Test TTS
```python
audio_url = service.text_to_speech("Hello, this is a test.")
print(audio_url)  # Returns base64 encoded audio
```

---

## Benefits of Deepgram Over Whisper

1. **No Local Installation**: Cloud-based API, no need to install large models
2. **Smart Formatting**: Automatic punctuation and capitalization
3. **Faster Processing**: Cloud infrastructure optimized for speed
4. **Built-in TTS**: Single API for both STT and TTS
5. **Better Timestamps**: More accurate word-level timestamps
6. **Scalability**: Easy to scale without hardware limitations

---

## Troubleshooting

### Deepgram API Errors
- Check API key is correct in `.env`
- Ensure audio files are in supported formats (WAV, MP3, MP4)
- Check Deepgram API status

### Audio Playback Issues
- Ensure browser supports base64 audio
- Check audio format compatibility
- Verify TTS response is properly encoded

---

## Next Steps

1. Copy all frontend files from Speechably
2. Update branding from Speechably to SpeechLabs
3. Add audio playback to CoachChat component
4. Test full workflow: upload → analysis → coaching → audio feedback
5. Deploy to production

---

For questions or issues, refer to the README.md or create an issue on GitHub.
