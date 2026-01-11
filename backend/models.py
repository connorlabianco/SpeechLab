from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for Google OAuth authentication"""
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True)
    name = db.Column(db.String(255))
    picture = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    
    analyses = db.relationship('Analysis', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'

class Analysis(db.Model):
    """Analysis model to store speech analysis results"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Metadata
    filename = db.Column(db.String(500))
    duration = db.Column(db.Float)
    
    # Analysis data (stored as JSON)
    emotion_segments = db.Column(db.JSON)
    transcription_data = db.Column(db.JSON)
    gemini_analysis = db.Column(db.JSON)
    
    # Quick access metrics
    dominant_emotion = db.Column(db.String(50))
    avg_wps = db.Column(db.Float)
    clarity_score = db.Column(db.Float)
    total_words = db.Column(db.Integer)
    
    # Additional metrics for quick access
    emotion_metrics = db.Column(db.JSON)
    speech_clarity = db.Column(db.JSON)
    wps_data = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Analysis {self.id} - {self.filename}>'

class PracticeSession(db.Model):
    """Practice conversation session with AI analysis"""
    __tablename__ = 'practice_session'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Session metadata
    duration = db.Column(db.Float)  # seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Conversation data
    transcript = db.Column(db.JSON)  # Full conversation array
    
    # Analysis results
    summary = db.Column(db.Text)
    filler_word_count = db.Column(db.Integer)
    filler_words_breakdown = db.Column(db.JSON)
    key_strengths = db.Column(db.JSON)  # Array of strings
    improvement_areas = db.Column(db.JSON)  # Array of strings
    
    # Metrics
    conversational_flow_score = db.Column(db.Float)  # 0-100
    topic_coherence = db.Column(db.String(50))  # high/medium/low
    engagement_level = db.Column(db.String(50))  # high/medium/low
    avg_response_length_words = db.Column(db.Integer)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('practice_sessions', lazy=True))
    
    def __repr__(self):
        return f'<PracticeSession {self.id} - User {self.user_id}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'duration': self.duration,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'summary': self.summary,
            'filler_word_count': self.filler_word_count,
            'filler_words_breakdown': self.filler_words_breakdown,
            'key_strengths': self.key_strengths,
            'improvement_areas': self.improvement_areas,
            'conversational_flow_score': self.conversational_flow_score,
            'topic_coherence': self.topic_coherence,
            'engagement_level': self.engagement_level,
            'avg_response_length_words': self.avg_response_length_words
        }
