import google.generativeai as genai
import json
import re
import os
import sys
import statistics
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

class GeminiService:
    """
    Service class for interacting with the Gemini API to generate feedback
    for speech analysis.
    """
    
    def __init__(self, api_key: Optional[str] = None, debug_mode: bool = True):
        """
        Initialize the Gemini service with optional API key.

        Args:
            api_key: The Gemini API key. If None, attempts to load from environment.
            debug_mode: If True, saves all Gemini responses to a debug log file.
        """
        self.model = self.init_gemini(api_key)
        self.debug_mode = debug_mode

        # Set up debug log directory
        if self.debug_mode:
            self.debug_log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs', 'gemini_debug')
            os.makedirs(self.debug_log_dir, exist_ok=True)
            print(f"Debug mode enabled. Logs will be saved to: {self.debug_log_dir}", file=sys.stderr)

        # Log init status
        if self.model is None:
            print("WARNING: Gemini model initialization failed. Analysis will be limited.", file=sys.stderr)
        else:
            print("Gemini model initialized successfully.")
    
    def init_gemini(self, api_key: Optional[str] = None) -> Any:
        """
        Initialize the Gemini API client.
        
        Args:
            api_key: The Gemini API key. If None, attempts to load from environment.
            
        Returns:
            The Gemini model or None if initialization fails.
        """
        try:
            # Get API key from parameter or environment variable
            API_KEY = api_key or os.environ.get("GEMINI_API_KEY")
            
            # Debug: Check if API key is loaded
            if not API_KEY:
                print("ERROR: GEMINI_API_KEY not found in environment variables or parameters", file=sys.stderr)
                print(f"DEBUG: Checking environment - GEMINI_API_KEY in os.environ: {'GEMINI_API_KEY' in os.environ}", file=sys.stderr)
                if 'GEMINI_API_KEY' in os.environ:
                    key_value = os.environ.get("GEMINI_API_KEY")
                    print(f"DEBUG: GEMINI_API_KEY value length: {len(key_value) if key_value else 0}", file=sys.stderr)
                    print(f"DEBUG: GEMINI_API_KEY starts with: {key_value[:10] if key_value and len(key_value) > 10 else 'N/A'}...", file=sys.stderr)
                return None
            else:
                print(f"DEBUG: GEMINI_API_KEY loaded successfully (length: {len(API_KEY)})", file=sys.stderr)
                print(f"DEBUG: GEMINI_API_KEY starts with: {API_KEY[:10]}...", file=sys.stderr)
                
            # Configure the API client
            genai.configure(api_key=API_KEY)
            
            # Set up the model - NO TOKEN LIMITS
            # Set max_output_tokens to maximum allowed (64,000 for gemini-3-flash)
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 64000,  # Maximum allowed - NO LIMITS
            }
            
            # Disable all safety filters for speech analysis
            # BLOCK_NONE allows all content through for analysis purposes
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            # Create the model - use correct model name
            # Try gemini-3-flash-preview first (correct name), fallback to gemini-1.5-flash if needed
            model = None
            model_names_to_try = [
                "gemini-3-flash-preview",  # Correct name for Gemini 3 Flash
                "gemini-1.5-flash",  # Fallback if preview not available
                "gemini-pro"  # Final fallback
            ]
            
            last_error = None
            for model_name in model_names_to_try:
                try:
                    print(f"Attempting to initialize model: {model_name}", file=sys.stderr)
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        generation_config=generation_config,
                        safety_settings=safety_settings
                    )
                    print(f"Successfully created model: {model_name}", file=sys.stderr)
                    break
                except Exception as model_error:
                    print(f"Failed to create model {model_name}: {str(model_error)}", file=sys.stderr)
                    last_error = model_error
                    continue
            
            if model is None:
                raise Exception(f"Failed to initialize any Gemini model. Last error: {str(last_error)}")
            
            # Test the model with a simple call to verify it's actually working
            try:
                print("Testing Gemini model with a simple API call...", file=sys.stderr)
                test_response = model.generate_content("Hello")
                if not test_response:
                    raise Exception("Model did not return a response for test call")
                if not hasattr(test_response, 'text'):
                    raise Exception("Model response is missing text attribute")
                if not test_response.text:
                    raise Exception("Model response text is empty")
                print(f"Gemini model test successful. Response: {test_response.text[:50]}...", file=sys.stderr)
            except Exception as test_error:
                error_msg = str(test_error)
                print(f"Gemini model test call failed: {error_msg}", file=sys.stderr)
                # Check for specific error types
                if "API key" in error_msg or "403" in error_msg or "401" in error_msg:
                    raise Exception(f"API key authentication failed: {error_msg}. Check that your GEMINI_API_KEY is valid and the Generative Language API is enabled.")
                elif "404" in error_msg or "not found" in error_msg.lower():
                    raise Exception(f"Model not found: {error_msg}. The model name may be incorrect or not available in your region.")
                elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
                    raise Exception(f"Quota or billing issue: {error_msg}. Check your Google Cloud billing and quotas.")
                else:
                    raise Exception(f"Model initialization test failed: {error_msg}")
                
            return model
        except Exception as e:
            print(f"Error initializing Gemini: {str(e)}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return None
    
    def generate_speech_analysis_prompt(self, transcription_data: List[Dict[str, Any]]) -> str:
        """
        Generate a formatted prompt for Gemini based on speech analysis.
        
        Args:
            transcription_data: List of transcription segment dictionaries
            
        Returns:
            Formatted prompt string for Gemini
        """
        # Create the formatted timeline for reference
        timeline_blocks = []
        issues = []
        
        # Format time helper function
        def format_time(seconds: float) -> str:
            minutes = int(seconds // 60)
            seconds_remainder = int(seconds % 60)
            return f"{minutes:02d}:{seconds_remainder:02d}"
        
        for segment in transcription_data:
            # Format times
            start_time = format_time(segment["start"])
            end_time = format_time(segment["end"])
            
            # Create formatted block
            block = (
                f"{start_time}-{end_time} | "
                f"WPS: {segment['wps']:.2f} | "
                f"Emotion: {segment['emotion']} | "
                f"Text: \"{segment['text']}\""
            )
            
            timeline_blocks.append(block)
            
            # Check for issues
            if segment["wps"] > 3.0:
                issues.append(f"- Segment at {start_time}-{end_time} is too fast ({segment['wps']:.2f} WPS)")
            elif segment["wps"] < 1.0:
                issues.append(f"- Segment at {start_time}-{end_time} is too slow ({segment['wps']:.2f} WPS)")
        
        # Calculate WPS statistics
        wps_values = [segment["wps"] for segment in transcription_data]
        avg_wps = sum(wps_values) / len(wps_values) if wps_values else 0
        # Calculate standard deviation for variation (more meaningful than range)
        # Typical standard deviation for natural speech is around 0.3-0.7 WPS
        wps_variation = statistics.stdev(wps_values) if len(wps_values) > 1 else 0
        
        # Count emotion transitions
        emotion_transitions = 0
        for i in range(1, len(transcription_data)):
            if transcription_data[i]["emotion"] != transcription_data[i-1]["emotion"]:
                emotion_transitions += 1
        
        # Build the prompt
        prompt = f"""You are a professional speech coach analyzing speech transcript data. The following is a timeline of speech segments with transcriptions, speaking rate (words per second), and detected emotions:

{chr(10).join(block for block in timeline_blocks)}

Based on this data, provide constructive feedback on:

1. Speaking Rate:
   - Average speaking rate: {avg_wps:.2f} WPS (optimal is 2.0-3.0 WPS)
   - Rate variation: {wps_variation:.2f} WPS (higher variation can indicate better engagement)
   - Specific segments to improve:
     {chr(10).join(f'     {issue}' for issue in issues) if issues else '     None identified'}

2. Emotional Expression:
   - Number of emotion transitions: {emotion_transitions}
   - Evaluate whether the emotions match the content of each segment
   - Suggest where emotional variety could improve engagement

3. Clarity and Enunciation:
   - Identify any unclear or nonsensical phrases that suggest poor enunciation. (If words are spoken too fast, or too quietly, or pronounced incorrectly, they may be unclear on the transcription. Please assume that the user's speech is written correctly, and that the transcription looking incorrect is due to the user speaking too fast, or too quietly, or pronounced incorrectly. This is mostly fixed by enunciating more clearly and slowing down.)
   - Suggest specific techniques to improve clarity

4. Overall Presentation:
   - Provide 3-5 specific action items to improve this speech
   - Suggest a practice exercise tailored to this speaker's needs

IMPORTANT: Respond ONLY with valid JSON. Do not include any explanatory text, markdown formatting, or code blocks. Return ONLY the JSON object itself.

Your response must be EXACTLY in this JSON structure:
{{
  "summary": "Your overall analysis and key observations",
  "improvement_areas": ["Area 1", "Area 2", "Area 3"],
  "strengths": ["Strength 1", "Strength 2"],
  "coaching_tips": ["Tip 1", "Tip 2", "Tip 3"]
}}"""
        
        return prompt
    
    def generate_simple_prompt(self, emotion_segments: List[Tuple[str, str]]) -> str:
        """
        Generate a simpler prompt when transcription data is not available.
        
        Args:
            emotion_segments: List of (time_range, emotion) tuples
            
        Returns:
            Formatted prompt string for Gemini
        """
        # Format emotion segments for context
        emotion_timeline = "\n".join([f"{time_range}: {emotion}" for time_range, emotion in emotion_segments])
        
        prompt = f"""You are a professional speech coach helping someone improve their communication skills.
Analyze the following emotion timeline from a speech:

{emotion_timeline}

Based on this emotional pattern:
1. Provide a brief summary of the speaker's emotional journey
2. Identify 3 specific areas for improvement
3. Point out 2-3 emotional strengths
4. Give 3-5 practical coaching tips to help the speaker improve

IMPORTANT: Respond ONLY with valid JSON. Do not include any explanatory text, markdown formatting, or code blocks. Return ONLY the JSON object itself.

Your response must be EXACTLY in this JSON structure:
{{
  "summary": "Your overall analysis and key observations",
  "improvement_areas": ["Area 1", "Area 2", "Area 3"],
  "strengths": ["Strength 1", "Strength 2"],
  "coaching_tips": ["Tip 1", "Tip 2", "Tip 3"]
}}"""
        
        return prompt
    
    def _save_debug_log(self, response_text: str, prompt: str, success: bool, error_msg: Optional[str] = None):
        """
        Save a debug log of the Gemini response for troubleshooting.
        """
        if not self.debug_mode:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        status = "SUCCESS" if success else "FAILED"
        filename = f"gemini_response_{status}_{timestamp}.txt"
        filepath = os.path.join(self.debug_log_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"GEMINI DEBUG LOG - {status}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write("=" * 80 + "\n\n")

                f.write("PROMPT SENT:\n")
                f.write("-" * 80 + "\n")
                f.write(prompt + "\n")
                f.write("-" * 80 + "\n\n")

                f.write("RAW RESPONSE:\n")
                f.write("-" * 80 + "\n")
                f.write(response_text + "\n")
                f.write("-" * 80 + "\n\n")

                if error_msg:
                    f.write("ERROR MESSAGE:\n")
                    f.write("-" * 80 + "\n")
                    f.write(error_msg + "\n")
                    f.write("-" * 80 + "\n\n")

                f.write(f"Response length: {len(response_text)} characters\n")

            print(f"Debug log saved to: {filepath}", file=sys.stderr)
        except Exception as e:
            print(f"Failed to save debug log: {str(e)}", file=sys.stderr)

    def _extract_json_from_response(self, response_text: str, emotion_segments: List[Tuple[str, str]], prompt: str = "") -> Dict[str, Any]:
        """
        Extract JSON from Gemini response text with robust error handling.
        """
        # Clean the response text
        cleaned_text = response_text.strip()

        # Try to repair common JSON malformations
        repaired_text = cleaned_text
        if repaired_text.endswith('"}') and not repaired_text.endswith('"]}'):
            open_brackets = repaired_text.count('[')
            close_brackets = repaired_text.count(']')
            if open_brackets > close_brackets:
                repaired_text = repaired_text[:-1] + '"]}'
                print("Attempted to repair malformed JSON by adding missing ]", file=sys.stderr)

        # Try multiple extraction strategies
        extraction_strategies = [
            lambda text: json.loads(text),
            lambda text: json.loads(text.strip()),
            lambda text: json.loads(re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL).group(1)),
            lambda text: json.loads(re.search(r'```\s*(.*?)\s*```', text, re.DOTALL).group(1)),
            lambda text: json.loads(re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL).group(0)),
            lambda text: json.loads(re.search(r'\{.*\}', text, re.DOTALL).group(0)),
        ]

        for i, strategy in enumerate(extraction_strategies):
            try:
                result = strategy(repaired_text)
                if isinstance(result, dict) and all(key in result for key in ["summary", "improvement_areas", "strengths", "coaching_tips"]):
                    print(f"Successfully parsed JSON using strategy {i+1}", file=sys.stderr)
                    self._save_debug_log(response_text, prompt, success=True)
                    return result
            except (json.JSONDecodeError, AttributeError, TypeError, KeyError) as e:
                continue

        # If all strategies fail, use fallback
        error_msg = "Failed to parse JSON from Gemini response after trying all strategies."
        print(error_msg, file=sys.stderr)
        print(f"Response text (first 500 chars): {response_text[:500]}", file=sys.stderr)
        print(f"Response text length: {len(response_text)}", file=sys.stderr)
        self._save_debug_log(response_text, prompt, success=False, error_msg=error_msg)
        return self.generate_fallback_analysis(emotion_segments)

    def generate_fallback_analysis(self, emotion_segments: List[Tuple[str, str]]) -> Dict[str, Any]:
        """
        Generate a fallback analysis when Gemini is not available.
        """
        # Count emotions
        emotion_counts = {}
        for _, emotion in emotion_segments:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # Find dominant emotion
        dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else "unknown"
        
        # Count transitions
        transitions = 0
        prev_emotion = None
        for _, emotion in emotion_segments:
            if prev_emotion and prev_emotion != emotion:
                transitions += 1
            prev_emotion = emotion
        
        # Basic analysis
        analysis = {
            "summary": "Based on the emotion patterns detected in your speech, here are some basic observations and suggestions for improvement.",
            "improvement_areas": [
                "Work on maintaining consistent emotional tone when appropriate",
                "Practice transitioning smoothly between different emotional states",
                "Focus on matching your emotional tone to your content"
            ],
            "strengths": [
                f"You showed a predominant {dominant_emotion} tone throughout your speech",
                f"You had {transitions} emotional transitions, showing some emotional range"
            ],
            "coaching_tips": [
                "Record yourself speaking regularly and review your emotional patterns",
                "Practice speaking with deliberate emotional tones to expand your range",
                "Ask for feedback from others about how your emotions come across",
                "Try mirroring techniques to build emotional awareness in your speech",
                "Join a speaking club like Toastmasters to get regular speaking practice"
            ]
        }
        
        return analysis
    
    def analyze_speech(
        self, 
        emotion_segments: List[Tuple[str, str]], 
        transcription_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Use Gemini to analyze speech patterns and provide coaching feedback.
        """
        if self.model is None:
            print("Using fallback analysis because Gemini model is not available", file=sys.stderr)
            return self.generate_fallback_analysis(emotion_segments)
        
        # Generate appropriate prompt based on available data
        if transcription_data:
            prompt = self.generate_speech_analysis_prompt(transcription_data)
        else:
            prompt = self.generate_simple_prompt(emotion_segments)
        
        try:
            # Verify model is still available before making the call
            if self.model is None:
                raise Exception("Gemini model is None - cannot generate content")
            if not hasattr(self.model, 'generate_content'):
                raise Exception("Gemini model missing generate_content method")
            
            # Get response from Gemini
            response = self.model.generate_content(prompt)
            if not response:
                raise Exception("Gemini returned None response")
            if not hasattr(response, 'text'):
                raise Exception("Gemini response missing text attribute")
            response_text = response.text

            # Extract JSON data from response
            analysis_data = self._extract_json_from_response(response_text, emotion_segments, prompt)

            return analysis_data
            
        except Exception as e:
            print(f"Error during Gemini analysis: {str(e)}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return self.generate_fallback_analysis(emotion_segments)
            
    def generate_chat_response(self, user_input: str, emotion_context: str) -> str:
        """
        Generate a chat response for the AI coach feature.
        """
        if not self.model:
            return "I'm currently limited to basic responses as my AI analysis capabilities are offline. Here are some general tips: speak at a moderate pace (2-3 words per second), practice with recordings to improve tone, and join speaking clubs for regular feedback."
            
        # Create prompt for Gemini
        prompt = f"""You are a supportive and knowledgeable speech coach helping someone improve their communication.

The user's speech had these emotional patterns:
{emotion_context}

The user is asking: "{user_input}"

Provide helpful, specific coaching advice related to their question. Be encouraging but honest.
Keep your response concise (3-5 sentences) unless detailed instructions are needed."""
        
        try:
            # Get response from Gemini
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating chat response: {str(e)}", file=sys.stderr)
            return "I'm having trouble generating a personalized response right now. Here's some general advice: focus on maintaining a consistent pace, practice in front of a mirror to work on your delivery, and record yourself to identify specific areas for improvement."
