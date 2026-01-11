from flask import Blueprint, request, jsonify, current_app
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

# Create blueprint
api_bp = Blueprint('api', __name__)

# Get API keys from environment
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
DEEPGRAM_API_KEY = os.environ.get('DEEPGRAM_API_KEY')

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found in environment variables", file=sys.stderr)
    load_dotenv()
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

if not DEEPGRAM_API_KEY:
    print("WARNING: DEEPGRAM_API_KEY not found in environment variables", file=sys.stderr)
    load_dotenv()
    DEEPGRAM_API_KEY = os.environ.get('DEEPGRAM_API_KEY')

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

@api_bp.route('/upload', methods=['POST'])
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
            
            # Create response data
            response_data = {
                'success': True,
                'video_id': unique_id,
                'emotion_segments': [{'time_range': tr, 'emotion': e} for tr, e in emotion_segments],
                'transcription_data': transcription_data,
                'gemini_analysis': gemini_analysis,
                'emotion_metrics': emotion_metrics,
                'speech_clarity': speech_clarity if transcription_data else None,
                'wps_data': json.loads(wps_data.to_json(orient='records')) if wps_data is not None else None,
                'duration': total_duration
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
def chat_with_coach():
    """Handle chat requests to the AI coach"""
    try:
        data = request.json
        user_input = data.get('message', '')
        emotion_segments = data.get('emotion_segments', [])
        
        # Format emotion context for Gemini
        emotion_context = "\n".join([f"{seg['time_range']}: {seg['emotion']}" 
                                    for seg in emotion_segments])
        
        # Generate response from Gemini
        response = gemini_service.generate_chat_response(user_input, emotion_context)
        
        # Generate audio feedback using Deepgram TTS
        audio_url = None
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

@api_bp.route('/generate-analysis-audio', methods=['POST'])
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

@api_bp.route('/healthcheck', methods=['GET'])
def healthcheck():
    """Simple health check endpoint"""
    # Check service status
    gemini_status = "available" if gemini_service.model is not None else "unavailable"
    deepgram_status = "available" if deepgram_service.client is not None else "unavailable"
    
    return jsonify({
        'status': 'ok',
        'services': {
            'gemini': gemini_status,
            'deepgram': deepgram_status
        }
    }), 200
