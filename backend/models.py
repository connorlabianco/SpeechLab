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
