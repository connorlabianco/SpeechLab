# SpeechLabs

**Creating confidence through user-driven feedback.**  
Advanced speech analysis powered by AI.  
Perfect for public speaking, presentations, interviews, or confidence-building exercises.

---

## Overview

**SpeechLabs** is a comprehensive AI-powered speech analysis platform that evaluates videos of users speaking. It analyzes **speech emotion**, **delivery patterns**, provides **real-time transcription**, generates **personalized AI feedback**, and offers **text-to-speech coaching**. The platform includes **user authentication**, **analysis history**, and **PDF report generation** for tracking progress over time.

---

## Key Features

- **Video Upload & Processing** – Users upload videos of themselves speaking for analysis
- **Speech Emotion Recognition** – Detects tone, mood, and speaking style using Hugging Face Wav2Vec2 models
- **Speaking Rate Analysis** – Measures words per second (WPS) and provides visual feedback on pacing
- **AI-Powered Feedback** – Gemini AI generates comprehensive insights and personalized coaching tips
- **Interactive AI Speech Coach** – Chatbot for personalized advice based on analysis patterns
- **Text-to-Speech Feedback** – Deepgram TTS reads coaching advice aloud with natural voice
- **Interactive Visualizations** – Recharts-powered emotion timelines and speaking rate graphs
- **Google OAuth Authentication** – Secure user login with Google accounts
- **Analysis History & Dashboard** – SQLite database stores all analyses for progress tracking
- **PDF Export** – Generate professional PDF reports of speech analyses

---

## Complete Tech Stack

### **Backend Framework & Server**
- **Flask 3.1.2** – Python web framework for REST API
- **Gunicorn 23.0.0** – Production WSGI HTTP server
- **Flask-CORS 6.0.2** – Cross-Origin Resource Sharing for frontend communication
- **Python 3.8+** – Core programming language

### **AI & Machine Learning**
- **Google Gemini API (gemini-2.0-flash-exp)** – Large language model for feedback generation and coaching
- **Hugging Face Transformers 4.40.0+** – Speech emotion recognition pipeline
- **Wav2Vec2** – Pre-trained model: `r-f/wav2vec-english-speech-emotion-recognition`
- **PyTorch 2.5.0+** – Deep learning framework for model inference
- **TorchAudio 2.5.0+** – Audio processing for PyTorch

### **Speech Processing**
- **Deepgram SDK 5.0.0+** – Cloud-based speech-to-text and text-to-speech API
  - **Speech-to-Text (STT)**: Nova-2 model with Smart Formatting
  - **Text-to-Speech (TTS)**: Aura-Asteria-EN model for natural voice synthesis
- **FFmpeg** – Audio/video extraction and segmentation
- **SoundFile 0.12.1+** – Audio file I/O operations

### **Database & Authentication**
- **SQLite** – Lightweight relational database for user data and analysis storage
- **Flask-SQLAlchemy 3.1.1** – ORM for database operations
- **Flask-Login 0.6.3** – User session management
- **Authlib 1.3.0+** – OAuth 2.0 client library
- **Google OAuth 2.0** – Secure authentication with Google accounts

### **Data Processing & Analysis**
- **NumPy 1.26.0+** – Numerical computing and array operations
- **Pandas 2.2.0+** – Data manipulation and analysis
- **Statistics (Python stdlib)** – Statistical calculations for speech metrics

### **Document Generation**
- **ReportLab 4.0.0+** – PDF generation for analysis reports
- **Plotly 5.24.0+** – Visualization library (backend support)

### **Configuration & Utilities**
- **python-dotenv 1.0.1** – Environment variable management
- **Werkzeug 3.1.3** – WSGI utility library

### **Frontend Framework**
- **React 18.2.0** – JavaScript library for building user interfaces
- **React Router DOM 6.10.0** – Client-side routing and navigation
- **Node.js 14+** – JavaScript runtime for development

### **Frontend Visualization**
- **Recharts 2.5.0** – Composable charting library for React
  - Emotion timeline visualizations
  - Speaking rate (WPS) charts
  - Emotion distribution pie charts

### **Frontend Styling**
- **CSS3** – Modern styling with custom properties and animations
- **CSS Modules** – Component-scoped styling

---

## Detailed Architecture

### Backend Services

#### 1. **Audio Service** (`backend/services/audio_service.py`)
- Video-to-audio extraction using FFmpeg
- Audio segmentation for parallel processing
- Duration calculation and timestamp management

#### 2. **Deepgram Service** (`backend/services/deepgram_service.py`)
- **Speech-to-Text**: Transcribes audio segments with timestamps
- **Text-to-Speech**: Converts text feedback to natural-sounding audio
- Smart formatting for punctuation and capitalization
- Speaking rate metrics calculation

#### 3. **Speech Analysis Service** (`backend/services/speech_analysis.py`)
- Emotion recognition using Wav2Vec2 model
- 10 emotion categories: angry, calm, sad, surprised, happy, neutral, anxious, disappointed, fearful, excited
- Batch processing of audio segments

#### 4. **Gemini Service** (`backend/services/gemini_service.py`)
- Comprehensive speech analysis generation
- Interactive coaching chat responses
- JSON-formatted insights and recommendations
- Fallback analysis for error handling

#### 5. **Database Models** (`backend/models.py`)
- **User Model**: Google OAuth user information
- **Analysis Model**: Complete speech analysis records with metrics

#### 6. **PDF Generator** (`backend/utils/pdf_generator.py`)
- Professional PDF report generation
- Formatted tables and charts
- Analysis summary, strengths, improvements, tips

#### 7. **Data Processor** (`backend/utils/data_processor.py`)
- Audio duration detection
- Emotion timeline formatting
- Analysis results aggregation

#### 8. **Visualization Helper** (`backend/utils/visualization.py`)
- Emotion metrics calculation
- WPS (words per second) data preparation
- Chart data formatting for frontend

### Frontend Components

#### **Layout Components**
- **Header** – Navigation and branding
- **Footer** – Copyright and links
- **Card** – Reusable container component
- **Loading** – Loading state indicators
- **TabPanel** – Tabbed interface for analysis views

#### **Feature Components**
- **VideoUploader** – Drag-and-drop video upload with validation
- **EmotionTimeline** – Interactive emotion visualization chart
- **TranscriptView** – Formatted transcript display with timestamps
- **InsightPanel** – AI-generated analysis insights display
- **CoachChat** – Interactive chatbot with audio playback
- **FeatureList** – Landing page feature showcase

#### **Pages**
- **Home** – Landing page with features
- **Analysis** – Complete analysis results dashboard
- **NotFound** – 404 error page

#### **Services**
- **API Client** (`frontend/src/services/api.js`) – Centralized API communication

---

## API Endpoints

### **Authentication**
- `GET /api/login` – Initiate Google OAuth login
- `GET /api/authorize` – Handle OAuth callback
- `POST /api/logout` – Log out current user
- `GET /api/user` – Get current user information

### **Analysis**
- `POST /api/upload` – Upload video and analyze (requires authentication)
- `POST /api/chat` – Chat with AI coach (requires authentication)
- `POST /api/generate-analysis-audio` – Generate TTS audio for analysis sections
- `GET /api/dashboard` – Get user's analysis history (requires authentication)
- `GET /api/analysis/<id>` – Get specific analysis details (requires authentication)
- `GET /api/analysis/<id>/export-pdf` – Download PDF report (requires authentication)

### **Health Check**
- `GET /api/healthcheck` – Check API server and service status

---

## Environment Configuration

### Required Environment Variables

Create a `.env` file in the `backend` directory:

```env
# AI API Keys
GEMINI_API_KEY=your_gemini_api_key_here
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# Google OAuth (optional - for authentication features)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
OAUTH_REDIRECT_URI=http://localhost:5000/api/authorize

# Flask Configuration
SECRET_KEY=your_secret_key_here
FLASK_ENV=development
FLASK_DEBUG=True

# Database (optional - defaults to SQLite)
DATABASE_URL=sqlite:///speech_analysis.db

# Frontend URL (for OAuth redirects)
FRONTEND_URL=http://localhost:3000

# Audio Processing
FFMPEG_PATH=ffmpeg  # Only if FFmpeg not in PATH
```

---

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Node.js 14 or higher
- FFmpeg installed and in system PATH
- Google Gemini API key
- Deepgram API key
- (Optional) Google OAuth credentials for authentication

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd speechlabs/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

5. **Initialize database** (automatic on first run)
   ```bash
   python app.py
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd ../frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm start
   ```

### Running the Application

1. **Start backend** (Terminal 1)
   ```bash
   cd backend
   python app.py
   ```
   Backend runs on `http://localhost:5000`

2. **Start frontend** (Terminal 2)
   ```bash
   cd frontend
   npm start
   ```
   Frontend runs on `http://localhost:3000`

3. **Access application**
   Open `http://localhost:3000` in your browser

---

## Project Structure

```
speechlabs/
├── backend/                          # Flask Backend
│   ├── api/                          # API routes
│   │   ├── __init__.py
│   │   └── routes.py                 # All API endpoints
│   │
│   ├── services/                     # Core business logic
│   │   ├── __init__.py
│   │   ├── audio_service.py          # FFmpeg audio processing
│   │   ├── deepgram_service.py       # Deepgram STT/TTS integration
│   │   ├── gemini_service.py         # Gemini AI integration
│   │   └── speech_analysis.py        # Wav2Vec2 emotion recognition
│   │
│   ├── utils/                        # Utility functions
│   │   ├── __init__.py
│   │   ├── data_processor.py         # Data processing & formatting
│   │   ├── visualization.py          # Visualization data prep
│   │   └── pdf_generator.py          # PDF report generation
│   │
│   ├── models.py                     # SQLAlchemy database models
│   ├── app.py                        # Flask application factory
│   ├── requirements.txt              # Python dependencies
│   ├── .env.example                  # Environment template
│   └── .env                          # Environment variables (create this)
│
├── frontend/                         # React Frontend
│   ├── public/                       # Static assets
│   │   ├── index.html
│   │   ├── manifest.json
│   │   └── favicon.ico
│   │
│   ├── src/                          # Source code
│   │   ├── components/               # React components
│   │   │   ├── layout/               # Layout components
│   │   │   │   ├── Card.js
│   │   │   │   ├── Header.js
│   │   │   │   ├── Footer.js
│   │   │   │   ├── Loading.js
│   │   │   │   └── TabPanel.js
│   │   │   │
│   │   │   ├── CoachChat.js          # AI coach chatbot
│   │   │   ├── EmotionTimeline.js    # Emotion visualization
│   │   │   ├── FeatureList.js        # Feature cards
│   │   │   ├── InsightPanel.js       # Analysis insights
│   │   │   ├── TranscriptView.js     # Transcript display
│   │   │   └── VideoUploader.js      # Video upload interface
│   │   │
│   │   ├── pages/                    # Page components
│   │   │   ├── Home.js               # Landing page
│   │   │   ├── Analysis.js            # Analysis dashboard
│   │   │   └── NotFound.js            # 404 page
│   │   │
│   │   ├── services/                 # API services
│   │   │   └── api.js                # API client
│   │   │
│   │   ├── styles/                   # CSS stylesheets
│   │   │   ├── App.css
│   │   │   ├── components/           # Component styles
│   │   │   └── pages/                # Page styles
│   │   │
│   │   ├── App.js                    # Root component
│   │   └── index.js                  # Entry point
│   │
│   └── package.json                  # Node dependencies
│
├── README.md                         # This file
├── SETUP_GUIDE.md                    # Detailed setup instructions
├── MIGRATION_GUIDE.md                # Migration documentation
├── OAUTH_SETUP.md                    # OAuth setup guide
└── PROJECT_STRUCTURE.md              # Project structure details
```

---

## Data Flow Architecture

1. **Video Upload**: User uploads video → Flask receives and saves file
2. **Audio Extraction**: FFmpeg extracts audio from video
3. **Segmentation**: Audio split into ~30-second segments for processing
4. **Parallel Processing**:
   - **Deepgram**: Transcribes each segment with timestamps
   - **Wav2Vec2**: Analyzes emotion for each segment
5. **Metrics Calculation**: WPS, clarity scores, emotion distributions
6. **AI Analysis**: Gemini generates comprehensive feedback
7. **Database Storage**: Save analysis to SQLite linked to user
8. **Frontend Display**: React components visualize results
9. **Interactive Features**:
   - Chat with AI coach (Gemini responses)
   - Audio playback (Deepgram TTS)
   - PDF export (ReportLab generation)

---

## Speech Analysis Features

### Emotion Recognition
- **10 Emotion Categories**: angry, calm, sad, surprised, happy, neutral, anxious, disappointed, fearful, excited
- **Model**: Wav2Vec2 from Hugging Face
- **Accuracy**: Pre-trained on speech emotion datasets

### Speaking Rate Analysis
- **Optimal Range**: 2.0-3.0 words per second (WPS)
- **Metrics**:
  - Average WPS across all segments
  - WPS variation (standard deviation)
  - Fast segments identification (>3.0 WPS)
  - Slow segments identification (<1.0 WPS)

### Transcription Quality
- **Deepgram Nova-2 Model**
- **Smart Formatting**: Automatic punctuation and capitalization
- **Timestamps**: Word-level and segment-level timing
- **Languages**: Optimized for English

### AI Feedback Components
1. **Summary**: Overall speech performance assessment
2. **Strengths**: Positive aspects identified
3. **Improvement Areas**: Specific areas to work on
4. **Coaching Tips**: Actionable recommendations
5. **Practice Exercises**: Suggested activities

---

## Security & Privacy

- **Authentication**: Google OAuth 2.0 for secure login
- **Session Management**: Flask-Login with secure cookies
- **Data Isolation**: Users can only access their own analyses
- **CORS Protection**: Configured for frontend domain only
- **File Upload Limits**: 700MB maximum file size
- **Input Validation**: All inputs sanitized and validated

---

## Browser Compatibility

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

---

## Troubleshooting

### FFmpeg Issues
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/ and add to PATH
```

### API Key Errors
- Verify keys are correctly set in `.env`
- Ensure `.env` is in `backend/` directory
- Restart Flask server after updating `.env`

### Module Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Database Errors
```bash
# Delete and recreate database
rm backend/speech_analysis.db
python backend/app.py  # Automatically creates new database
```

### OAuth Issues
- Verify Google OAuth credentials in `.env`
- Check redirect URI matches Google Console configuration
- Ensure cookies are enabled in browser

---

## Performance Optimization

- **Audio Segmentation**: Parallel processing of segments
- **Cloud APIs**: Deepgram for faster transcription vs local Whisper
- **Caching**: Analysis results stored in database
- **Lazy Loading**: Frontend components load progressively

---

## Future Enhancements

- Real-time speech analysis during recording
- Custom coaching goals and progress tracking
- Mobile app (React Native)
- Multi-language support
- Advanced analytics dashboard with trends
- Peer comparison and community features
- Live practice mode with instant feedback
- Gamification and achievements system

---

## License & Copyright

**© 2026 SpeechLabs. All Rights Reserved.**

This software is proprietary and confidential. Unauthorized copying, distribution, modification, or use of this software, via any medium, is strictly prohibited without express written permission from the copyright holder.

**Commercial use of this software or any derivatives is prohibited without a valid commercial license.**

For licensing inquiries, contact the project owner.

---

## Acknowledgments

- **Deepgram** – Excellent Speech-to-Text and Text-to-Speech APIs
- **Google** – Gemini AI API for feedback generation
- **Hugging Face** – Pre-trained Wav2Vec2 emotion recognition models
- **Open Source Community** – For the amazing tools and libraries

---

**SpeechLabs** - Professional speech analysis and coaching platform.
