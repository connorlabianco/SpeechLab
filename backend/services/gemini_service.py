import google.generativeai as genai
import json
import re
import os
import sys
from typing import Dict, List, Tuple, Any, Optional, Union
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
            if not API_KEY:
                print("GEMINI_API_KEY not found in environment variables or parameters", file=sys.stderr)
                print("Environment variables:", {k: v for k, v in os.environ.items() if 'API' in k}, file=sys.stderr)
                return None
                
            # Configure the API client
            genai.configure(api_key=API_KEY)
            
            # Set up the model
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                # No max_output_tokens limit - allow Gemini to generate complete responses
            }
            
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
            
            # Try to create the model
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Test the model with a simple call to verify it works
            test_response = model.generate_content("Hello")
            if not test_response:
                raise Exception("Model did not return a response for test call")
                
            return model
        except Exception as e:
            print(f"Error initializing Gemini: {str(e)}", file=sys.stderr)
            # Print the full exception traceback for debugging
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
        wps_variation = max(wps_values) - min(wps_values) if wps_values else 0
        
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
        
        prompt = f"""
You are a professional speech coach helping someone improve their communication skills.
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
}}
"""
        return prompt
    
    def _save_debug_log(self, response_text: str, prompt: str, success: bool, error_msg: Optional[str] = None):
        """
        Save a debug log of the Gemini response for troubleshooting.

        Args:
            response_text: The raw response from Gemini
            prompt: The prompt sent to Gemini
            success: Whether JSON parsing was successful
            error_msg: Optional error message if parsing failed
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

        Args:
            response_text: The raw response text from Gemini
            emotion_segments: Emotion segments for fallback analysis if needed
            prompt: The original prompt sent (for debug logging)

        Returns:
            Dictionary containing parsed JSON or fallback analysis
        """
        # Clean the response text
        cleaned_text = response_text.strip()

        # Try to repair common JSON malformations (e.g., missing closing brackets)
        repaired_text = cleaned_text
        # If the text ends with "} but not "]}, try adding the missing ]
        if repaired_text.endswith('"}') and not repaired_text.endswith('"]}'):
            # Check if we're likely inside an array that needs closing
            # Count opening [ vs closing ] to see if we're missing one
            open_brackets = repaired_text.count('[')
            close_brackets = repaired_text.count(']')
            if open_brackets > close_brackets:
                repaired_text = repaired_text[:-1] + '"]}'
                print("Attempted to repair malformed JSON by adding missing ]", file=sys.stderr)

        # Try multiple extraction strategies in order of likelihood
        extraction_strategies = [
            # Strategy 1: Direct JSON parsing (response is pure JSON)
            lambda text: json.loads(text),

            # Strategy 1b: Direct JSON parsing after stripping whitespace
            lambda text: json.loads(text.strip()),

            # Strategy 2: Extract from ```json code block
            lambda text: json.loads(re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL).group(1)),

            # Strategy 3: Extract from ``` code block (without json marker)
            lambda text: json.loads(re.search(r'```\s*(.*?)\s*```', text, re.DOTALL).group(1)),

            # Strategy 4: Find first complete JSON object with curly braces
            lambda text: json.loads(re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL).group(0)),

            # Strategy 5: Find any JSON-like structure (greedy)
            lambda text: json.loads(re.search(r'\{.*\}', text, re.DOTALL).group(0)),
        ]

        for i, strategy in enumerate(extraction_strategies):
            try:
                result = strategy(repaired_text)
                # Validate the result has required fields
                if isinstance(result, dict) and all(key in result for key in ["summary", "improvement_areas", "strengths", "coaching_tips"]):
                    print(f"Successfully parsed JSON using strategy {i+1}", file=sys.stderr)
                    self._save_debug_log(response_text, prompt, success=True)
                    return result
                else:
                    print(f"Strategy {i+1} parsed but validation failed. Type: {type(result)}, Keys: {result.keys() if isinstance(result, dict) else 'N/A'}", file=sys.stderr)
            except (json.JSONDecodeError, AttributeError, TypeError, KeyError) as e:
                print(f"Strategy {i+1} failed: {type(e).__name__}: {str(e)[:100]}", file=sys.stderr)
                continue

        # If all strategies fail, log the error and use fallback
        error_msg = "Failed to parse JSON from Gemini response after trying all strategies."
        print(error_msg, file=sys.stderr)
        print(f"Raw response (first 1000 chars): {response_text[:1000]}", file=sys.stderr)
        self._save_debug_log(response_text, prompt, success=False, error_msg=error_msg)
        return self.generate_fallback_analysis(emotion_segments)

    def generate_fallback_analysis(self, emotion_segments: List[Tuple[str, str]]) -> Dict[str, Any]:
        """
        Generate a fallback analysis when Gemini is not available.
        This provides basic insights using local logic rather than the LLM.
        
        Args:
            emotion_segments: List of (time_range, emotion) tuples
            
        Returns:
            Dictionary containing basic analysis results
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
        
        Args:
            emotion_segments: List of (time_range, emotion) tuples
            transcription_data: Optional list of transcription segment dictionaries
            
        Returns:
            Dictionary containing analysis results
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
            # Get response from Gemini
            response = self.model.generate_content(prompt)
            response_text = response.text

            # Check if response was truncated
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason'):
                    finish_reason = str(candidate.finish_reason)
                    if 'MAX_TOKENS' in finish_reason or 'LENGTH' in finish_reason:
                        print(f"WARNING: Gemini response was truncated due to token limit. Finish reason: {finish_reason}", file=sys.stderr)
                        print("Consider increasing max_output_tokens in generation_config", file=sys.stderr)

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
        
        Args:
            user_input: The user's question or message
            emotion_context: Formatted string describing the emotion context
            
        Returns:
            The AI coach's response text
        """
        if not self.model:
            return "I'm currently limited to basic responses as my AI analysis capabilities are offline. Here are some general tips: speak at a moderate pace (2-3 words per second), practice with recordings to improve tone, and join speaking clubs for regular feedback. For more personalized advice, please check your API settings or try again later."
            
        # Create prompt for Gemini
        prompt = f"""
You are a supportive and knowledgeable speech coach helping someone improve their communication.

The user's speech had these emotional patterns:
{emotion_context}

The user is asking: "{user_input}"

Provide helpful, specific coaching advice related to their question. Be encouraging but honest.
Keep your response concise (3-5 sentences) unless detailed instructions are needed.
"""
        
        try:
            # Get response from Gemini
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            # Provide a fallback response if Gemini fails
            print(f"Error generating chat response: {str(e)}", file=sys.stderr)
            return "I'm having trouble generating a personalized response right now. Here's some general advice: focus on maintaining a consistent pace, practice in front of a mirror to work on your delivery, and record yourself to identify specific areas for improvement. Would you like advice on a particular aspect of public speaking?"