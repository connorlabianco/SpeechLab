from flask import Blueprint, request, jsonify, current_app, redirect, url_for, send_file
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
import os
import uuid
import tempfile
from werkzeug.utils import secure_filename
import json
import sys
from dotenv import load_dotenv

from services.audio_service import AudioSegmenter, AudioSegmenterConfig
from services.speech_analysis import SpeechAnalyzer
from services.deepgram_service import DeepgramService
from services.gemini_service import GeminiService
from utils.data_processor import DataProcessor
from utils.visualization import VisualizationHelper
from utils.pdf_generator import SpeechAnalysisPDF
from models import db, User, Analysis, PracticeSession

# Create blueprint
api_bp = Blueprint('api', __name__)

# Get API keys from environment
# Note: .env should already be loaded by app.py, but reload if needed
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
DEEPGRAM_API_KEY = os.environ.get('DEEPGRAM_API_KEY')

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found in environment variables, attempting to reload .env", file=sys.stderr)
    # Try loading from backend/.env specifically
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(backend_dir, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Loaded .env from: {env_path}", file=sys.stderr)
    else:
        load_dotenv()  # Try current directory
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    if GEMINI_API_KEY:
        print("GEMINI_API_KEY loaded after reload", file=sys.stderr)
    else:
        print("ERROR: GEMINI_API_KEY still not found after reload", file=sys.stderr)

if not DEEPGRAM_API_KEY:
    print("WARNING: DEEPGRAM_API_KEY not found in environment variables, attempting to reload .env", file=sys.stderr)
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(backend_dir, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv()
    DEEPGRAM_API_KEY = os.environ.get('DEEPGRAM_API_KEY')
    if DEEPGRAM_API_KEY:
        print("DEEPGRAM_API_KEY loaded after reload", file=sys.stderr)
    else:
        print("ERROR: DEEPGRAM_API_KEY still not found after reload", file=sys.stderr)

# Initialize services
speech_analyzer = SpeechAnalyzer()
deepgram_service = DeepgramService(api_key=DEEPGRAM_API_KEY)
gemini_service = GeminiService(api_key=GEMINI_API_KEY)
visualization_helper = VisualizationHelper()

# Configure audio segmenter
FFMPEG_PATH = os.environ.get('FFMPEG_PATH', 'ffmpeg')
print(f"Using FFmpeg: {FFMPEG_PATH}", file=sys.stderr)

audio_config = AudioSegmenterConfig(ffmpeg_path=FFMPEG_PATH)
audio_segmenter = AudioSegmenter(audio_config)
data_processor = DataProcessor(FFMPEG_PATH)

def allowed_file(filename):
    """Check if file has an allowed extension"""
    ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'webm', 'mp3', 'wav'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# OAuth Routes
@api_bp.route('/login')
def login():
    """Initiate Google OAuth login"""
    google = current_app.config.get('GOOGLE_OAUTH')
    if not google:
        return jsonify({'error': 'OAuth not configured'}), 500
    
    # Use explicit redirect URI from config if set, otherwise generate from url_for
    redirect_uri = current_app.config.get('OAUTH_REDIRECT_URI')
    if not redirect_uri:
        redirect_uri = url_for('api.authorize', _external=True)
    
    # Debug: Print the redirect URI being used
    print(f"OAuth redirect URI: {redirect_uri}", file=sys.stderr)
    return google.authorize_redirect(redirect_uri)

@api_bp.route('/authorize')
def authorize():
    """Handle OAuth callback"""
    google = current_app.config.get('GOOGLE_OAUTH')
    if not google:
        return jsonify({'error': 'OAuth not configured'}), 500
    
    # Check for OAuth errors
    error = request.args.get('error')
    if error:
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
        return redirect(f'{frontend_url}/login?error={error}')
    
    try:
        token = google.authorize_access_token()
        if not token:
            return jsonify({'error': 'Failed to get access token'}), 400
        
        user_info = token.get('userinfo')
        
        if user_info:
            user = User.query.filter_by(google_id=user_info['sub']).first()
            
            if not user:
                user = User(
                    google_id=user_info['sub'],
                    email=user_info.get('email'),
                    name=user_info.get('name'),
                    picture=user_info.get('picture')
                )
                db.session.add(user)
            else:
                # Update user info
                user.email = user_info.get('email', user.email)
                user.name = user_info.get('name', user.name)
                user.picture = user_info.get('picture', user.picture)
                user.last_login = datetime.utcnow()
            
            db.session.commit()
            login_user(user)
            
            # Redirect to frontend with success indicator
            frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
            return redirect(f'{frontend_url}/login?success=true')
        
        return jsonify({'error': 'Failed to get user info'}), 400
    
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': f'Authentication failed: {str(e)}'}), 500

@api_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout the current user"""
    logout_user()
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200

@api_bp.route('/user', methods=['GET'])
@login_required
def get_current_user():
    """Get current user information"""
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'name': current_user.name,
        'picture': current_user.picture
    }), 200

@api_bp.route('/upload', methods=['POST'])
@login_required
def upload_video():
    """
    Handle video upload and processing
    Returns analysis results including emotion segments and transcription
    """
    # Check if file part exists
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    # Check if filename is empty
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Check if file type is allowed
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Create a unique filename
    filename = secure_filename(file.filename)
    unique_id = str(uuid.uuid4())
    unique_filename = f"{unique_id}_{filename}"
    
    # Save uploaded file
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(upload_path)
    
    # Create a temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Create output directory for segments
            output_dir = os.path.join(temp_dir, "output_segments")
            os.makedirs(output_dir, exist_ok=True)
            
            # Extract and split audio
            full_audio_path, segment_paths = audio_segmenter.extract_and_split_audio(upload_path, output_dir)
            
            # Get total duration of the full audio
            total_duration = data_processor.get_audio_duration(full_audio_path)
            
            # Analyze the segments for emotions
            results = speech_analyzer.analyze_segments(output_dir)
            
            # Get segment durations
            segment_durations = [data_processor.get_audio_duration(path) for path in segment_paths]
            
            # Process emotion data into time-based segments
            emotion_segments = data_processor.process_emotion_data(
                results, 
                total_duration, 
                segment_durations
            )
            
            # Calculate average segment duration (for WPS)
            average_segment_duration = total_duration / len(segment_paths) if segment_paths else 0
            
            # Transcribe segments using Deepgram
            transcription_data = deepgram_service.transcribe_segments(
                segment_paths, 
                average_segment_duration,
                emotion_data=emotion_segments
            )
            
            # Generate LLM insights
            gemini_analysis = gemini_service.analyze_speech(emotion_segments, transcription_data)
            
            # Log the analysis result
            print(f"Gemini analysis summary: {gemini_analysis.get('summary', 'Not available')[:100]}...", file=sys.stderr)
            
            # Save all analysis results to a file
            results_path = data_processor.save_analysis_results(
                output_dir, 
                emotion_segments, 
                transcription_data,
                gemini_analysis
            )
            
            # Prepare visualization data
            emotion_df = visualization_helper.prepare_emotion_timeline_data(emotion_segments)
            emotion_metrics = visualization_helper.calculate_emotion_metrics(emotion_df)
            wps_data = None
            speech_clarity = None
            
            if transcription_data:
                wps_data = visualization_helper.prepare_wps_data(transcription_data)
                speech_clarity = visualization_helper.prepare_speech_clarity_data(transcription_data)
            
            # Prepare emotion segments for database (convert tuples to dicts)
            emotion_segments_dict = [{'time_range': tr, 'emotion': e} for tr, e in emotion_segments]
            
            # Calculate metrics for database storage
            dominant_emotion = emotion_metrics.get('main_emotion', 'neutral') if emotion_metrics else 'neutral'
            avg_wps = speech_clarity.get('avg_wps', 0) if speech_clarity else 0
            clarity_score = speech_clarity.get('clarity_score', 0) if speech_clarity else 0
            total_words = speech_clarity.get('total_words', 0) if speech_clarity else 0
            
            # Save analysis to database
            analysis = Analysis(
                user_id=current_user.id,
                filename=file.filename,
                duration=total_duration,
                emotion_segments=emotion_segments_dict,
                transcription_data=transcription_data,
                gemini_analysis=gemini_analysis,
                dominant_emotion=dominant_emotion,
                avg_wps=avg_wps,
                clarity_score=clarity_score,
                total_words=total_words,
                emotion_metrics=emotion_metrics,
                speech_clarity=speech_clarity if transcription_data else None,
                wps_data=json.loads(wps_data.to_json(orient='records')) if wps_data is not None else None
            )
            
            db.session.add(analysis)
            db.session.commit()
            
            # Create response data
            response_data = {
                'success': True,
                'analysis_id': analysis.id,
                'video_id': unique_id,
                'emotion_segments': emotion_segments_dict,
                'transcription_data': transcription_data,
                'gemini_analysis': gemini_analysis,
                'emotion_metrics': emotion_metrics,
                'speech_clarity': speech_clarity if transcription_data else None,
                'wps_data': json.loads(wps_data.to_json(orient='records')) if wps_data is not None else None,
                'duration': total_duration,
                'redirect_url': f'/analysis/{analysis.id}'
            }
            
            return jsonify(response_data), 200
            
        except Exception as e:
            import traceback
            traceback.print_exc(file=sys.stderr)
            return jsonify({'error': str(e)}), 500
        
        finally:
            # Clean up the uploaded file
            if os.path.exists(upload_path):
                os.remove(upload_path)

@api_bp.route('/chat', methods=['POST'])
@login_required
def chat_with_coach():
    """Handle chat requests to the AI coach"""
    try:
        data = request.json
        user_input = data.get('message', '')
        emotion_segments = data.get('emotion_segments', [])
        include_audio = data.get('include_audio', False)
        
        # Format emotion context for Gemini
        emotion_context = "\n".join([f"{seg['time_range']}: {seg['emotion']}" 
                                    for seg in emotion_segments])
        
        # Generate response from Gemini
        response = gemini_service.generate_chat_response(user_input, emotion_context)
        
        # Generate audio feedback using Deepgram TTS only if requested
        audio_url = None
        if include_audio:
            try:
                audio_url = deepgram_service.text_to_speech(response)
            except Exception as e:
                print(f"Warning: TTS generation failed: {str(e)}", file=sys.stderr)
        
        return jsonify({
            'response': response,
            'audio_url': audio_url
        }), 200
    
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500

@api_bp.route('/chat-voice', methods=['POST'])
@login_required
def chat_with_coach_voice():
    """Handle voice chat - transcribe audio, get Gemini response, return TTS audio"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        emotion_segments = json.loads(request.form.get('emotion_segments', '[]'))
        
        # Save to temp file
        temp_audio_path = os.path.join(tempfile.gettempdir(), f"voice_{uuid.uuid4().hex}.webm")
        audio_file.save(temp_audio_path)
        
        print(f"Saved audio to: {temp_audio_path}, size: {os.path.getsize(temp_audio_path)} bytes", file=sys.stderr)
        
        try:
            # Use the new transcription method
            transcription_result = deepgram_service.transcribe_audio_file(temp_audio_path)
            
            if not transcription_result.get('success'):
                error = transcription_result.get('error', 'Unknown error')
                print(f"Transcription failed: {error}", file=sys.stderr)
                return jsonify({'error': f'Transcription failed: {error}'}), 500
            
            user_text = transcription_result.get('transcript', '').strip()
            
            if not user_text:
                return jsonify({'error': 'No speech detected in audio'}), 400
            
            print(f"User said: '{user_text}'", file=sys.stderr)
            
            # Get Gemini response
            emotion_context = "\n".join([f"{seg.get('time_range', '')}: {seg.get('emotion', '')}" 
                                        for seg in emotion_segments])
            coach_response = gemini_service.generate_chat_response(user_text, emotion_context)
            
            print(f"Coach response: '{coach_response[:100]}...'", file=sys.stderr)
            
            # Generate TTS
            audio_url = deepgram_service.text_to_speech(coach_response)
            
            return jsonify({
                'user_text': user_text,
                'response': coach_response,
                'audio_url': audio_url,
                'success': True
            }), 200
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
    
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500

@api_bp.route('/generate-analysis-audio', methods=['POST'])
@login_required
def generate_analysis_audio():
    """Generate audio narration of Gemini analysis using Deepgram TTS
    
    Supports generating audio for specific sections:
    - 'summary': Summary section only
    - 'strengths': Strengths section only
    - 'improvements': Areas for improvement section only
    - 'tips': Coaching tips section only
    - None or 'all': All sections combined (default)
    """
    try:
        data = request.json
        gemini_analysis = data.get('gemini_analysis', {})
        section = data.get('section', 'all')  # Get the requested section
        
        if not gemini_analysis:
            return jsonify({'error': 'No analysis data provided'}), 400
        
        # Build text based on requested section
        text_to_speak = None
        
        if section == 'summary':
            if gemini_analysis.get('summary'):
                text_to_speak = f"Summary: {gemini_analysis['summary']}"
            else:
                return jsonify({'error': 'Summary section not available'}), 400
                
        elif section == 'strengths':
            if gemini_analysis.get('strengths') and len(gemini_analysis['strengths']) > 0:
                strengths_text = "Your strengths include: " + ", ".join(gemini_analysis['strengths'])
                text_to_speak = strengths_text
            else:
                return jsonify({'error': 'Strengths section not available'}), 400
                
        elif section == 'improvements':
            if gemini_analysis.get('improvement_areas') and len(gemini_analysis.get('improvement_areas', [])) > 0:
                improvements_text = "Areas for improvement: " + ", ".join(gemini_analysis['improvement_areas'])
                text_to_speak = improvements_text
            else:
                return jsonify({'error': 'Improvement areas section not available'}), 400
                
        elif section == 'tips':
            if gemini_analysis.get('coaching_tips') and len(gemini_analysis['coaching_tips']) > 0:
                tips_list = []
                for i, tip in enumerate(gemini_analysis['coaching_tips'], 1):
                    tip_text = tip if isinstance(tip, str) else (tip.get('tip', '') if isinstance(tip, dict) else str(tip))
                    tips_list.append(f"Tip {i}: {tip_text}")
                text_to_speak = "Here are some coaching tips: " + ". ".join(tips_list)
            else:
                return jsonify({'error': 'Coaching tips section not available'}), 400
                
        else:  # 'all' or default - combine all sections
            text_parts = []
            
            if gemini_analysis.get('summary'):
                text_parts.append(f"Summary: {gemini_analysis['summary']}")
            
            if gemini_analysis.get('strengths') and len(gemini_analysis['strengths']) > 0:
                strengths_text = "Your strengths include: " + ", ".join(gemini_analysis['strengths'])
                text_parts.append(strengths_text)
            
            if gemini_analysis.get('improvement_areas') and len(gemini_analysis['improvement_areas']) > 0:
                improvements_text = "Areas for improvement: " + ", ".join(gemini_analysis['improvement_areas'])
                text_parts.append(improvements_text)
            
            if gemini_analysis.get('coaching_tips') and len(gemini_analysis['coaching_tips']) > 0:
                tips_list = []
                for i, tip in enumerate(gemini_analysis['coaching_tips'], 1):
                    tip_text = tip if isinstance(tip, str) else (tip.get('tip', '') if isinstance(tip, dict) else str(tip))
                    tips_list.append(f"Tip {i}: {tip_text}")
                tips_text = "Here are some coaching tips: " + ". ".join(tips_list)
                text_parts.append(tips_text)
            
            if not text_parts:
                return jsonify({'error': 'No valid analysis content to convert to audio'}), 400
            
            text_to_speak = ". ".join(text_parts)
        
        if not text_to_speak or not text_to_speak.strip():
            return jsonify({'error': 'No text content available for the requested section'}), 400
        
        # Generate audio using Deepgram TTS
        try:
            # The text_to_speech method now handles temp files and returns base64 directly
            audio_data = deepgram_service.text_to_speech(text_to_speak)
            
            # Return base64 encoded audio
            return jsonify({
                'audio_data': audio_data,
                'success': True,
                'section': section
            }), 200
            
        except ValueError as e:
            # Client not initialized or empty text
            error_msg = str(e)
            print(f"TTS validation error: {error_msg}", file=sys.stderr)
            return jsonify({'error': f'Failed to generate audio: {error_msg}'}), 400
        except Exception as e:
            error_msg = str(e)
            print(f"Error generating audio: {error_msg}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return jsonify({'error': f'Failed to generate audio: {error_msg}'}), 500
    
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500

@api_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """Get all analyses for the current user"""
    analyses = Analysis.query.filter_by(user_id=current_user.id)\
        .order_by(Analysis.created_at.desc()).all()
    
    analyses_data = []
    for analysis in analyses:
        analyses_data.append({
            'id': analysis.id,
            'filename': analysis.filename,
            'duration': analysis.duration,
            'dominant_emotion': analysis.dominant_emotion,
            'avg_wps': analysis.avg_wps,
            'clarity_score': analysis.clarity_score,
            'total_words': analysis.total_words,
            'created_at': analysis.created_at.isoformat() if analysis.created_at else None
        })
    
    return jsonify({
        'success': True,
        'analyses': analyses_data,
        'total': len(analyses_data)
    }), 200

@api_bp.route('/analysis/<int:analysis_id>', methods=['GET'])
@login_required
def get_analysis(analysis_id):
    """Get a specific analysis by ID"""
    analysis = Analysis.query.get_or_404(analysis_id)
    
    # Check if user owns this analysis
    if analysis.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({
        'success': True,
        'analysis': {
            'id': analysis.id,
            'filename': analysis.filename,
            'duration': analysis.duration,
            'emotion_segments': analysis.emotion_segments,
            'transcription_data': analysis.transcription_data,
            'gemini_analysis': analysis.gemini_analysis,
            'dominant_emotion': analysis.dominant_emotion,
            'avg_wps': analysis.avg_wps,
            'clarity_score': analysis.clarity_score,
            'total_words': analysis.total_words,
            'emotion_metrics': analysis.emotion_metrics,
            'speech_clarity': analysis.speech_clarity,
            'wps_data': analysis.wps_data,
            'created_at': analysis.created_at.isoformat() if analysis.created_at else None
        }
    }), 200

@api_bp.route('/analysis/<int:analysis_id>/export-pdf', methods=['GET'])
@login_required
def export_pdf(analysis_id):
    """Export analysis as PDF"""
    analysis = Analysis.query.get_or_404(analysis_id)
    
    # Check if user owns this analysis
    if analysis.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        pdf_generator = SpeechAnalysisPDF()
        pdf_buffer = pdf_generator.generate_pdf(analysis, current_user)
        
        filename = f"speech_analysis_{analysis.id}_{analysis.filename or 'report'}.pdf"
        # Clean filename for filesystem
        filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': f'Failed to generate PDF: {str(e)}'}), 500

@api_bp.route('/deepgram-key', methods=['GET'])
@login_required
def get_deepgram_key():
    """Get Deepgram API key for frontend WebSocket connection"""
    if not DEEPGRAM_API_KEY:
        return jsonify({'error': 'Deepgram API key not configured'}), 500
    return jsonify({'api_key': DEEPGRAM_API_KEY}), 200

@api_bp.route('/analyze-conversation', methods=['POST'])
@login_required
def analyze_conversation():
    """
    Analyze a practice conversation using Gemini AI.
    Called by voice agent function: analyze_conversation_practice
    """
    try:
        data = request.json
        transcript = data.get('conversation_transcript', [])
        duration = data.get('duration_seconds', 0)
        
        if not transcript or len(transcript) < 2:
            return jsonify({
                'success': False,
                'error': 'Conversation too short to analyze'
            }), 400
        
        # Analyze using Gemini service
        gemini_service = GeminiService()
        analysis = gemini_service.analyze_conversation(transcript)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        }), 200
        
    except Exception as e:
        print(f"Error in analyze_conversation: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({
            'success': False,
            'error': 'Failed to analyze conversation'
        }), 500


@api_bp.route('/save-practice-history', methods=['POST'])
@login_required
def save_practice_history():
    """
    Save analyzed practice conversation to user's history.
    Called by voice agent function: save_conversation_to_history
    """
    try:
        data = request.json
        analysis = data.get('analysis', {})
        transcript = data.get('conversation_transcript', [])
        duration = data.get('duration_seconds', 0)
        
        if not analysis:
            return jsonify({
                'success': False,
                'error': 'No analysis data provided'
            }), 400
        
        # Parse analysis if it's a string
        if isinstance(analysis, str):
            import json
            analysis = json.loads(analysis)
        
        # Create new practice session
        session = PracticeSession(
            user_id=current_user.id,
            duration=float(duration),
            transcript=transcript,
            summary=analysis.get('summary', ''),
            filler_word_count=analysis.get('filler_word_count', 0),
            filler_words_breakdown=analysis.get('filler_words_breakdown', {}),
            key_strengths=analysis.get('key_strengths', []),
            improvement_areas=analysis.get('improvement_areas', []),
            conversational_flow_score=analysis.get('conversational_flow_score', 0),
            topic_coherence=analysis.get('topic_coherence', 'medium'),
            engagement_level=analysis.get('engagement_level', 'medium'),
            avg_response_length_words=analysis.get('avg_response_length_words', 0)
        )
        
        db.session.add(session)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'session_id': session.id,
            'message': 'Practice session saved to your history!',
            'created_at': session.created_at.isoformat() if session.created_at else None
        }), 200
        
    except Exception as e:
        print(f"Error in save_practice_history: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to save practice session'
        }), 500


@api_bp.route('/practice-history', methods=['GET'])
@login_required
def get_practice_history():
    """
    Get all practice sessions for current user.
    Used to display practice history in frontend.
    """
    try:
        sessions = PracticeSession.query.filter_by(user_id=current_user.id)\
            .order_by(PracticeSession.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'sessions': [session.to_dict() for session in sessions],
            'total': len(sessions)
        }), 200
        
    except Exception as e:
        print(f"Error in get_practice_history: {str(e)}", file=sys.stderr)
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve practice history'
        }), 500

@api_bp.route('/practice-session/<int:session_id>', methods=['GET'])
@login_required
def get_practice_session(session_id):
    """Get a specific practice session by ID"""
    try:
        session = PracticeSession.query.get_or_404(session_id)
        
        # Check if user owns this session
        if session.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        return jsonify({
            'success': True,
            'session': session.to_dict()
        }), 200
    except Exception as e:
        print(f"Error in get_practice_session: {str(e)}", file=sys.stderr)
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve practice session'
        }), 500

@api_bp.route('/healthcheck', methods=['GET'])
def healthcheck():
    """Simple health check endpoint"""
    # Check service status with detailed diagnostics
    gemini_status = "unavailable"
    gemini_details = {}
    
    if gemini_service.model is not None:
        gemini_status = "available"
        gemini_details['model_exists'] = True
        gemini_details['has_generate_content'] = hasattr(gemini_service.model, 'generate_content')
        
        # Try a quick test call to verify it actually works
        try:
            test_response = gemini_service.model.generate_content("Test")
            gemini_details['test_call_success'] = True
            gemini_details['test_response_has_text'] = hasattr(test_response, 'text') if test_response else False
        except Exception as e:
            gemini_status = "error"
            gemini_details['test_call_error'] = str(e)
    else:
        gemini_details['model_exists'] = False
        gemini_details['reason'] = "Model is None - check initialization logs"
    
    deepgram_status = "available" if deepgram_service.client is not None else "unavailable"
    
    return jsonify({
        'status': 'ok',
        'services': {
            'gemini': {
                'status': gemini_status,
                'details': gemini_details
            },
            'deepgram': deepgram_status
        }
    }), 200
