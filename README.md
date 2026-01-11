# SpeechLabs

**Creating confidence through user-driven feedback.**  
Advanced speech analysis powered by AI - at no cost.  
Perfect for public speaking, presentations, interviews, or confidence-building exercises.

---

## Overview

**SpeechLabs** is an AI-powered speech analysis tool that evaluates videos of users speaking. It analyzes **speech emotion** and **delivery patterns**, then generates personalized feedback using Google Gemini AI and provides transcription through Deepgram's Speech-to-Text API. The goal: help users overcome social anxiety, improve delivery, and speak with confidence.

---

## Key Features

- 🎥 **Video Upload** – Users upload a video of themselves speaking
- 🔊 **Speech Emotion Recognition** – Detects tone, mood, and speaking style using pre-trained models
- 📊 **Speaking Rate Analysis** – Measures words per second and provides visual feedback
- 🧠 **AI-Powered Feedback** – LLM-generated insights and tips to improve delivery using Google Gemini
- 💬 **AI Speech Coach** – Interactive chatbot for personalized advice based on your speech patterns
- 🔊 **Text-to-Speech Feedback** – Deepgram TTS reads coaching advice aloud
- 📈 **Interactive Visualizations** – View detailed timelines of emotion patterns and speaking rate

---

## Tech Stack

### Backend
- **Flask** – REST API backend
- **Python 3.8+** – Core logic
- **Hugging Face Transformers** – Speech emotion recognition (Wav2Vec2)
- **Deepgram API** – Speech-to-text transcription with Smart Formatting
- **Deepgram TTS** – Text-to-speech for audio feedback
- **Google Gemini API** – AI feedback generation
- **FFmpeg** – Audio extraction and processing

### Frontend
- **React** – User interface
- **React Router** – Client-side routing
- **Recharts** – Data visualization
- **CSS Modules** – Component styling

---

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 14+
- FFmpeg installed on your system
- Google Gemini API key
- Deepgram API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/speechlabs.git
   cd speechlabs
   ```

2. **Set up the backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Create a .env file in the backend directory**
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   DEEPGRAM_API_KEY=your_deepgram_api_key_here
   FFMPEG_PATH=ffmpeg  # Only if FFmpeg is not in your PATH
   ```

4. **Set up the frontend**
   ```bash
   cd ../frontend
   npm install
   ```

### Running the Application

1. **Start the Flask backend**
   ```bash
   cd backend
   python app.py
   ```
   The backend will run on `http://localhost:5000`

2. **Start the React frontend** (in a new terminal)
   ```bash
   cd frontend
   npm start
   ```
   The frontend will run on `http://localhost:3000`

3. **Open your browser and go to http://localhost:3000**

---

## Project Structure

```
speechlabs/
├── backend/                   # Flask backend
│   ├── api/                   # API routes
│   │   ├── __init__.py
│   │   └── routes.py          # Upload, chat, and health check endpoints
│   ├── services/              # Core services
│   │   ├── __init__.py
│   │   ├── audio_service.py   # Audio segmentation with FFmpeg
│   │   ├── deepgram_service.py # Deepgram STT and TTS
│   │   ├── gemini_service.py  # Gemini AI feedback generation
│   │   └── speech_analysis.py # Emotion recognition
│   ├── utils/                 # Utilities
│   │   ├── __init__.py
│   │   ├── data_processor.py  # Data processing and formatting
│   │   └── visualization.py   # Visualization data preparation
│   ├── app.py                 # Main Flask application
│   ├── requirements.txt       # Backend dependencies
│   └── .env.example           # Environment variables template
│
├── frontend/                  # React frontend
│   ├── public/                # Static files
│   │   ├── index.html
│   │   ├── manifest.json
│   │   └── favicon.ico
│   ├── src/                   # Source code
│   │   ├── components/        # Reusable UI components
│   │   │   ├── layout/        # Layout components
│   │   │   │   ├── Card.js
│   │   │   │   ├── Footer.js
│   │   │   │   ├── Header.js
│   │   │   │   ├── Loading.js
│   │   │   │   └── TabPanel.js
│   │   │   ├── CoachChat.js   # AI coach chatbot
│   │   │   ├── EmotionTimeline.js # Emotion visualization
│   │   │   ├── FeatureList.js # Feature cards
│   │   │   ├── InsightPanel.js # Analysis insights
│   │   │   ├── TranscriptView.js # Transcript display
│   │   │   └── VideoUploader.js # Video upload interface
│   │   ├── pages/             # Application pages
│   │   │   ├── Analysis.js    # Analysis results page
│   │   │   ├── Home.js        # Landing page
│   │   │   └── NotFound.js    # 404 page
│   │   ├── services/          # API client
│   │   │   └── api.js         # Backend API communication
│   │   ├── styles/            # CSS files
│   │   │   ├── components/
│   │   │   ├── pages/
│   │   │   └── App.css
│   │   ├── App.js             # Main React component
│   │   └── index.js           # Entry point
│   └── package.json           # Frontend dependencies
│
├── README.md                  # Project documentation
├── LICENSE                    # MIT License
└── .gitignore                 # Git ignore file
```

---

## API Endpoints

### POST /api/upload
Upload a video file for speech analysis.

**Request:**
- `file`: Video file (multipart/form-data)

**Response:**
```json
{
  "success": true,
  "video_id": "unique-id",
  "emotion_segments": [...],
  "transcription_data": [...],
  "gemini_analysis": {...},
  "emotion_metrics": {...},
  "speech_clarity": {...},
  "wps_data": [...],
  "duration": 120.5
}
```

### POST /api/chat
Interact with the AI speech coach.

**Request:**
```json
{
  "message": "How can I speak slower?",
  "emotion_segments": [...]
}
```

**Response:**
```json
{
  "response": "To speak slower, try...",
  "audio_url": "data:audio/wav;base64,..."
}
```

### GET /api/healthcheck
Check API server health.

**Response:**
```json
{
  "status": "ok",
  "services": {
    "gemini": "available",
    "deepgram": "available"
  }
}
```

---

## Features in Detail

### Speech Emotion Recognition
Uses the `r-f/wav2vec-english-speech-emotion-recognition` model from Hugging Face to detect emotions in speech segments including: angry, calm, sad, surprised, happy, neutral, anxious, disappointed, fearful, and excited.

### Deepgram Transcription
Utilizes Deepgram's Nova-2 model with Smart Formatting to provide:
- Accurate speech-to-text transcription
- Automatic punctuation
- Proper capitalization
- Timestamp data for each segment

### Speaking Rate Analysis
Calculates words per second (WPS) for each segment with:
- Optimal range indicators (2.0-3.0 WPS)
- Visual feedback (too fast, too slow, optimal)
- Variation metrics for engagement analysis

### Gemini AI Feedback
Generates comprehensive feedback including:
- Overall speech summary
- Identified strengths
- Areas for improvement
- Personalized coaching tips
- Practice exercises

### AI Speech Coach
Interactive chatbot powered by Gemini that:
- Answers specific questions about your speech
- Provides personalized coaching advice
- References your emotion patterns
- Offers audio feedback via Deepgram TTS

---

## Environment Variables

Create a `.env` file in the `backend` directory:

```env
# Required API Keys
GEMINI_API_KEY=your_gemini_api_key_here
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# Optional Configuration
FFMPEG_PATH=ffmpeg
FLASK_ENV=development
FLASK_DEBUG=True
```

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Special thanks to the open-source community for providing the tools and libraries that make this project possible
- Deepgram for their excellent Speech-to-Text and Text-to-Speech APIs
- Google for the Gemini AI API
- Hugging Face for pre-trained speech emotion recognition models
- Inspired by the need for accessible speech coaching tools for everyone

---

## Troubleshooting

### FFmpeg not found
Make sure FFmpeg is installed and in your system PATH:
- **macOS**: `brew install ffmpeg`
- **Ubuntu/Debian**: `sudo apt-get install ffmpeg`
- **Windows**: Download from https://ffmpeg.org/ and add to PATH

### API Key Issues
- Ensure your API keys are properly set in the `.env` file
- Check that the `.env` file is in the `backend` directory
- Restart the Flask server after updating `.env`

### Module Import Errors
- Make sure you've activated the virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python version (3.8+ required)

---

## Future Enhancements

- 📹 Real-time speech analysis during recording
- 🎯 Custom coaching goals and progress tracking
- 📱 Mobile app development
- 🌍 Multi-language support
- 📊 Advanced analytics dashboard
- 👥 Peer comparison features

---

For questions, issues, or feature requests, please open an issue on GitHub.
