import os
import sys
import base64
import tempfile
import uuid
import statistics
from typing import List, Dict, Tuple, Any, Optional
from deepgram import DeepgramClient

class DeepgramService:
    """
    Service for transcribing audio using the Deepgram Speech-to-Text API
    and generating speech using Deepgram Text-to-Speech API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Deepgram service with API key.
        
        Args:
            api_key: Deepgram API key. If None, attempts to load from environment.
        """
        self.api_key = api_key or os.environ.get('DEEPGRAM_API_KEY')
        self.client = self._initialize_client()
    
    def _initialize_client(self):
        """
        Initialize the Deepgram client.
        
        Returns:
            Deepgram client or None if initialization fails
        """
        try:
            if not self.api_key:
                print("DEEPGRAM_API_KEY not found in environment variables", file=sys.stderr)
                return None
            
            client = DeepgramClient(api_key=self.api_key)
            print("Successfully initialized Deepgram client")
            return client
        except Exception as e:
            print(f"Error initializing Deepgram client: {str(e)}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return None
    
    def transcribe_segments(
        self, 
        segment_paths: List[str], 
        segment_duration: float,
        emotion_data: Optional[List[Tuple[str, str]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Transcribe audio segments using the Deepgram API.
        
        Args:
            segment_paths: List of paths to audio segment files
            segment_duration: Approximate duration of each segment
            emotion_data: Optional list of (time_range, emotion) tuples
            
        Returns:
            List of dictionaries containing transcription data for each segment
        """
        if not self.client:
            print("Deepgram client not initialized. Cannot transcribe audio.")
            return []
        
        transcripts = []
        
        for i, segment_path in enumerate(segment_paths):
            if not os.path.exists(segment_path):
                print(f"Segment file not found: {segment_path}")
                continue
            
            try:
                # Get emotion from emotion_data if available
                emotion = emotion_data[i][1] if emotion_data and i < len(emotion_data) else "unknown"
                
                # Calculate segment times
                start_time = i * segment_duration
                end_time = (i + 1) * segment_duration
                
                # Read audio file
                with open(segment_path, 'rb') as audio_file:
                    buffer_data = audio_file.read()
                
                # Transcribe with Deepgram using new API (options as keyword arguments)
                response = self.client.listen.v1.media.transcribe_file(
                    request=buffer_data,
                    model="nova-2",
                    language="en",
                    smart_format=True,  # Enable Smart Formatting
                    punctuate=True,
                    paragraphs=False,
                    utterances=False,
                    diarize=False
                )
                
                # Extract transcript from response
                transcribed_text = ""
                if hasattr(response, 'results') and response.results:
                    channels = response.results.channels
                    if channels and len(channels) > 0:
                        alternatives = channels[0].alternatives
                        if alternatives and len(alternatives) > 0:
                            transcribed_text = alternatives[0].transcript.strip()
                
                # Count words and calculate WPS
                word_count = len(transcribed_text.split())
                wps = word_count / segment_duration if segment_duration > 0 else 0
                
                # Create segment data
                segment_data = {
                    "index": i,
                    "start": round(start_time, 2),
                    "end": round(end_time, 2),
                    "text": transcribed_text,
                    "wps": round(wps, 2),
                    "emotion": emotion
                }
                
                transcripts.append(segment_data)
                print(f"Transcribed segment {i+1}: {segment_data['text'][:50]}...")
                
            except Exception as e:
                error_type = type(e).__name__
                if 'Error' in error_type or 'deepgram' in str(type(e)).lower():
                    print(f"Deepgram API error transcribing segment {i+1}: {str(e)}", file=sys.stderr)
                else:
                    print(f"Error transcribing segment {i+1}: {str(e)}", file=sys.stderr)
                continue
        
        return transcripts
    
    def transcribe_full_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe a complete audio file with timestamps using Deepgram.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Dictionary containing full transcription with timestamps
        """
        if not self.client:
            print("Deepgram client not initialized. Cannot transcribe audio.")
            return {}
        
        try:
            # Read audio file
            with open(audio_path, 'rb') as audio_file:
                buffer_data = audio_file.read()
            
            # Transcribe with Deepgram using new API (options as keyword arguments)
            response = self.client.listen.v1.media.transcribe_file(
                request=buffer_data,
                model="nova-2",
                language="en",
                smart_format=True,
                punctuate=True,
                paragraphs=True,
                utterances=True,
                diarize=False
            )
            
            # Extract data from response
            result = {
                'transcript': '',
                'paragraphs': [],
                'utterances': [],
                'words': []
            }
            
            if hasattr(response, 'results') and response.results:
                channels = response.results.channels
                if channels and len(channels) > 0:
                    alternatives = channels[0].alternatives
                    if alternatives and len(alternatives) > 0:
                        result['transcript'] = alternatives[0].transcript
                        
                        # Get paragraphs if available
                        if hasattr(alternatives[0], 'paragraphs') and alternatives[0].paragraphs:
                            paragraphs = alternatives[0].paragraphs.paragraphs
                            result['paragraphs'] = [
                                {
                                    'text': p.text,
                                    'start': p.start,
                                    'end': p.end
                                } for p in paragraphs
                            ]
                        
                        # Get words with timestamps
                        if hasattr(alternatives[0], 'words') and alternatives[0].words:
                            result['words'] = [
                                {
                                    'word': w.word,
                                    'start': w.start,
                                    'end': w.end,
                                    'confidence': w.confidence
                                } for w in alternatives[0].words
                            ]
                
                # Get utterances if available
                if hasattr(response.results, 'utterances') and response.results.utterances:
                    result['utterances'] = [
                        {
                            'text': u.transcript,
                            'start': u.start,
                            'end': u.end,
                            'confidence': u.confidence
                        } for u in response.results.utterances
                    ]
            
            return result
            
        except Exception as e:
            error_type = type(e).__name__
            if 'Error' in error_type or 'deepgram' in str(type(e)).lower():
                print(f"Deepgram API error: {str(e)}", file=sys.stderr)
            else:
                print(f"Error transcribing audio: {str(e)}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return {}
    
    def text_to_speech(self, text: str, output_path: Optional[str] = None) -> str:
        """
        Convert text to speech using Deepgram TTS API.
        
        Args:
            text: Text to convert to speech
            output_path: Optional path to save audio file. If None, returns base64 audio.
            
        Returns:
            Path to saved audio file or base64 encoded audio data
            
        Raises:
            ValueError: If text is empty or client is not initialized
            Exception: If Deepgram API call fails or other errors during audio generation
        """
        if not self.client:
            error_msg = "Deepgram client not initialized. Cannot generate speech."
            print(error_msg, file=sys.stderr)
            raise ValueError(error_msg)
        
        if not text or not text.strip():
            error_msg = "Text cannot be empty for TTS generation."
            print(error_msg, file=sys.stderr)
            raise ValueError(error_msg)
        
        # Use a temporary file if no output path is provided
        temp_file = None
        if not output_path:
            temp_file = os.path.join(tempfile.gettempdir(), f"tts_temp_{uuid.uuid4().hex}.wav")
            output_path = temp_file
        
        try:
            # Generate speech using new API (options as keyword arguments)
            response = self.client.speak.v1.audio.generate(
                text=text,
                model="aura-asteria-en",  # Natural-sounding voice
                encoding="linear16",
                sample_rate=24000
            )
            
            # Write the audio stream to file
            with open(output_path, 'wb') as audio_file:
                audio_file.write(response.stream.getvalue())
            
            # Verify the file was created
            if not os.path.exists(output_path):
                error_msg = f"Audio file was not created at {output_path}"
                print(error_msg, file=sys.stderr)
                raise Exception(error_msg)
            
            # Check file size to ensure it's not empty
            file_size = os.path.getsize(output_path)
            if file_size == 0:
                error_msg = f"Generated audio file is empty (0 bytes)"
                print(error_msg, file=sys.stderr)
                raise Exception(error_msg)
            
            print(f"Audio generated successfully: {output_path} ({file_size} bytes)")
            
            # If temp file, read and convert to base64, then clean up
            if temp_file:
                try:
                    with open(output_path, 'rb') as audio_file:
                        audio_data = audio_file.read()
                        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                    
                    return f"data:audio/wav;base64,{audio_base64}"
                finally:
                    # Clean up temp file
                    if os.path.exists(output_path):
                        os.remove(output_path)
            else:
                return output_path
                
        except Exception as e:
            error_type = type(e).__name__
            if 'Error' in error_type or 'deepgram' in str(type(e)).lower():
                error_msg = f"Deepgram TTS API error: {str(e)}"
            else:
                error_msg = f"Error generating speech: {str(e)}"
            print(error_msg, file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            # Clean up temp file on error
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            raise Exception(error_msg) from e
    
    def get_speech_metrics(self, transcription_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate speech metrics based on transcription data.
        
        Args:
            transcription_data: List of transcription segment dictionaries
            
        Returns:
            Dictionary containing calculated speech metrics
        """
        if not transcription_data:
            return {
                "avg_wps": 0,
                "wps_variation": 0,
                "total_words": 0,
                "speech_clarity": 0,
                "fast_segments": [],
                "slow_segments": []
            }
        
        # Extract WPS values
        wps_values = [segment["wps"] for segment in transcription_data]
        
        # Calculate metrics
        avg_wps = sum(wps_values) / len(wps_values)
        
        # Calculate standard deviation for more meaningful variation metric
        # Standard deviation is more statistically meaningful than range
        # Typical standard deviation for natural speech is around 0.3-0.7 WPS
        wps_variation = statistics.stdev(wps_values) if len(wps_values) > 1 else 0
        total_words = sum(len(segment["text"].split()) for segment in transcription_data)
        
        # Identify segments that are too fast or too slow
        fast_segments = []
        slow_segments = []
        
        for i, segment in enumerate(transcription_data):
            if segment["wps"] > 3.0:
                fast_segments.append(i)
            elif segment["wps"] < 1.0:
                slow_segments.append(i)
        
        # Calculate speech clarity score
        avg_words_per_segment = total_words / len(transcription_data)
        clarity_score = min(100, max(0, (avg_words_per_segment / 20) * 100))
        
        return {
            "avg_wps": round(avg_wps, 2),
            "wps_variation": round(wps_variation, 2),
            "total_words": total_words,
            "speech_clarity": round(clarity_score, 1),
            "fast_segments": fast_segments,
            "slow_segments": slow_segments
        }
    
    def format_transcript_with_timestamps(self, transcription_data: List[Dict[str, Any]]) -> str:
        """
        Format the transcript data with timestamps for display.
        
        Args:
            transcription_data: List of transcription segment dictionaries
            
        Returns:
            Formatted transcript string with timestamps
        """
        if not transcription_data:
            return "No transcription data available."
        
        # Format time helper function
        def format_time(seconds: float) -> str:
            minutes = int(seconds // 60)
            seconds = int(seconds % 60)
            return f"{minutes:02d}:{seconds:02d}"
        
        # Build the formatted transcript
        formatted_lines = []
        
        for segment in transcription_data:
            start_time = format_time(segment["start"])
            end_time = format_time(segment["end"])
            
            line = f"[{start_time} - {end_time}] ({segment['emotion']}) {segment['text']}"
            formatted_lines.append(line)
        
        return "\n\n".join(formatted_lines)
