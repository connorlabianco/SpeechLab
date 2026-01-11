# Google OAuth & Database Integration Setup Guide

This document explains the OAuth authentication and database integration that has been added to your SpeechLab application.

## ✅ What Has Been Implemented

### 1. Database Models (`backend/models.py`)
- **User Model**: Stores Google OAuth user information
  - `google_id`: Unique Google user ID
  - `email`, `name`, `picture`: User profile information
  - `created_at`, `last_login`: Timestamps
  - Relationship to `Analysis` model

- **Analysis Model**: Stores speech analysis results
  - Links to user via `user_id`
  - Stores all analysis data (emotion segments, transcription, Gemini analysis)
  - Quick access metrics (dominant emotion, avg_wps, clarity_score, etc.)
  - Timestamps for when analysis was created

### 2. OAuth Authentication (`backend/api/routes.py`)
- **`/api/login`**: Initiates Google OAuth login flow
- **`/api/authorize`**: Handles OAuth callback and creates/updates user
- **`/api/logout`**: Logs out the current user (POST request)
- **`/api/user`**: Returns current user information (GET request)

### 3. Protected Routes
All analysis-related routes now require authentication:
- `/api/upload` - Video upload and processing (now saves to database)
- `/api/chat` - AI coach chat
- `/api/generate-analysis-audio` - Audio generation
- `/api/dashboard` - User's analysis history
- `/api/analysis/<id>` - View specific analysis
- `/api/analysis/<id>/export-pdf` - Export analysis as PDF

### 4. New API Endpoints

#### Dashboard
- **GET `/api/dashboard`**: Returns all analyses for the logged-in user
  - Returns: List of analyses with metadata (id, filename, duration, metrics, created_at)

#### Analysis Detail
- **GET `/api/analysis/<analysis_id>`**: Get full analysis data
  - Returns: Complete analysis including all segments, transcription, and Gemini insights
  - Protected: Users can only access their own analyses

#### PDF Export
- **GET `/api/analysis/<analysis_id>/export-pdf`**: Download analysis as PDF
  - Returns: PDF file with formatted report
  - Includes: User info, metrics, emotion timeline, transcription, AI insights

### 5. Database Integration
- The `/api/upload` endpoint now automatically saves analysis results to the database
- Each analysis is linked to the logged-in user
- Analysis data includes all metrics and visualization data for quick access

## 🔧 Setup Instructions

### Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

New dependencies added:
- `flask-sqlalchemy==3.1.1`
- `flask-login==0.6.3`
- `authlib>=1.3.0,<2.0.0`
- `reportlab>=4.0.0,<5.0.0`

### Step 2: Configure Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth client ID"
5. Configure OAuth consent screen:
   - User Type: External (or Internal if using Google Workspace)
   - App name: SpeechLab (or your preferred name)
   - Authorized domains: Add your domain (e.g., `localhost` for development)
6. Create OAuth 2.0 Client ID:
   - Application type: Web application
   - Name: SpeechLab Web Client
   - Authorized redirect URIs:
     - `http://localhost:5000/api/authorize` (for development)
     - `https://yourdomain.com/api/authorize` (for production)
7. Copy the Client ID and Client Secret

### Step 3: Update Environment Variables

Add these to your `backend/.env` file:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Flask Secret Key (generate a random string for production)
SECRET_KEY=your-secret-key-here

# Database (optional - defaults to sqlite:///backend/speech_analysis.db)
DATABASE_URL=sqlite:///speech_analysis.db
```

**Generate a secure SECRET_KEY:**
```python
import secrets
print(secrets.token_hex(32))
```

### Step 4: Initialize Database

The database will be automatically created when you first run the application. The SQLite database file will be created at:
- `backend/speech_analysis.db` (default)

To manually create tables (if needed):
```python
from app import create_app
from models import db

app = create_app()
with app.app_context():
    db.create_all()
```

### Step 5: Update Frontend

You'll need to update your frontend to:
1. Handle OAuth login flow
2. Store authentication state
3. Send credentials with API requests
4. Display dashboard and analysis history
5. Add PDF export button

**Example frontend changes needed:**

```javascript
// Add to your API service
export const login = async () => {
  window.location.href = `${API_BASE_URL}/login`;
};

export const logout = async () => {
  const response = await fetch(`${API_BASE_URL}/logout`, {
    method: 'POST',
    credentials: 'include'
  });
  return await response.json();
};

export const getCurrentUser = async () => {
  const response = await fetch(`${API_BASE_URL}/user`, {
    credentials: 'include'
  });
  if (response.status === 401) return null;
  return await response.json();
};

export const getDashboard = async () => {
  const response = await fetch(`${API_BASE_URL}/dashboard`, {
    credentials: 'include'
  });
  return await response.json();
};

export const getAnalysis = async (analysisId) => {
  const response = await fetch(`${API_BASE_URL}/analysis/${analysisId}`, {
    credentials: 'include'
  });
  return await response.json();
};

export const exportPDF = async (analysisId) => {
  const response = await fetch(`${API_BASE_URL}/analysis/${analysisId}/export-pdf`, {
    credentials: 'include'
  });
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `speech_analysis_${analysisId}.pdf`;
  a.click();
};
```

**Important:** Make sure your frontend sends credentials with requests:
- Add `credentials: 'include'` to all fetch requests
- Configure CORS properly (already done in `app.py`)

## 🔒 Security Features

1. **Route Protection**: All analysis routes require authentication
2. **User Isolation**: Users can only access their own analyses
3. **Session Management**: Flask-Login handles user sessions
4. **OAuth Security**: Uses Google's secure OAuth 2.0 flow

## 📊 Database Schema

### User Table
- `id` (Primary Key)
- `google_id` (Unique)
- `email`, `name`, `picture`
- `created_at`, `last_login`

### Analysis Table
- `id` (Primary Key)
- `user_id` (Foreign Key → User.id)
- `filename`, `duration`
- `emotion_segments` (JSON)
- `transcription_data` (JSON)
- `gemini_analysis` (JSON)
- `dominant_emotion`, `avg_wps`, `clarity_score`, `total_words`
- `emotion_metrics` (JSON)
- `speech_clarity` (JSON)
- `wps_data` (JSON)
- `created_at`

## 🚀 Testing

1. Start your Flask backend:
   ```bash
   cd backend
   python app.py
   ```

2. Test OAuth flow:
   - Navigate to `http://localhost:5000/api/login`
   - Should redirect to Google login
   - After login, should redirect back with user info

3. Test protected routes:
   - Try accessing `/api/dashboard` without login (should return 401)
   - Login first, then access dashboard (should return your analyses)

4. Test upload:
   - Upload a video (must be logged in)
   - Check database for new analysis entry
   - Verify analysis is linked to your user

5. Test PDF export:
   - Get an analysis ID from dashboard
   - Access `/api/analysis/<id>/export-pdf`
   - Should download a PDF file

## 📝 Notes

- The database uses SQLite by default (easy for development)
- For production, consider PostgreSQL or MySQL
- OAuth redirect URI must match exactly what's configured in Google Console
- Session cookies are used for authentication (configured with CORS)
- PDF generation uses ReportLab - reports include all analysis data formatted nicely

## 🐛 Troubleshooting

**OAuth not working:**
- Check that redirect URI matches exactly in Google Console
- Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are set correctly
- Check browser console for CORS errors

**Database errors:**
- Ensure SQLite database file is writable
- Check that models are imported correctly
- Verify database path in DATABASE_URL

**401 Unauthorized errors:**
- Make sure you're logged in
- Check that credentials are being sent with requests
- Verify session cookies are being set

**PDF generation errors:**
- Check that ReportLab is installed correctly
- Verify analysis data exists in database
- Check server logs for detailed error messages
