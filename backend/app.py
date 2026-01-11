from flask import Flask, jsonify
from flask_cors import CORS
import os
import sys
from dotenv import load_dotenv
from api.routes import api_bp

# Load environment variables
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, '.env')

try:
    if os.path.exists(ENV_PATH):
        load_dotenv(ENV_PATH)
        print(f"Loaded environment from: {ENV_PATH}", file=sys.stderr)
    else:
        print(f"Warning: .env file not found at {ENV_PATH}", file=sys.stderr)
        load_dotenv()
        print("Attempted to load .env from current directory", file=sys.stderr)
    
    # Check if API keys are loaded
    if 'GEMINI_API_KEY' in os.environ:
        print("GEMINI_API_KEY is set in environment", file=sys.stderr)
    else:
        print("WARNING: GEMINI_API_KEY is not set in environment", file=sys.stderr)
    
    if 'DEEPGRAM_API_KEY' in os.environ:
        print("DEEPGRAM_API_KEY is set in environment", file=sys.stderr)
    else:
        print("WARNING: DEEPGRAM_API_KEY is not set in environment", file=sys.stderr)
    
except Exception as e:
    print(f"Error loading environment variables: {str(e)}", file=sys.stderr)

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__, static_folder='../frontend/build', static_url_path='/')
    
    # Configure app
    app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
    app.config['TEMP_FOLDER'] = os.path.join(BASE_DIR, 'temp')
    app.config['MAX_CONTENT_LENGTH'] = 700 * 1024 * 1024  # Max 700MB uploads
    
    # Ensure upload and temp directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)
    
    # Enable CORS with specific configuration
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Serve React app at root
    @app.route('/')
    def index():
        return app.send_static_file('index.html')
    
    # Handle React routing
    @app.route('/<path:path>')
    def catch_all(path):
        return app.send_static_file('index.html')
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({'error': 'File is too large. Max size is 700MB.'}), 413
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
