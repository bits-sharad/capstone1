"""
Gemini LLM Service Integration
"""
import os
import json
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from dotenv import load_dotenv




load_dotenv()
class GeminiService:
    """Service for interacting with Google's Gemini API"""


    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash-lite"):
        """
        Initialize Gemini service


        Args:
            api_key: Google API key (if not provided, reads from GOOGLE_API_KEY env var)
            model_name: Name of the Gemini model to use
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key must be provided or set in GOOGLE_API_KEY environment variable")


        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
        self.chat_sessions = {}
        # Agents branch on this before calling the LLM (see agent *.analyze methods).
        self.enabled = True


    def generate_content(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Generate content using Gemini


        Args:
            prompt: The prompt to send to Gemini
            temperature: Temperature for response generation


        Returns:
            Generated text response
        """
        try:
            generation_config = {
                "temperature": temperature,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8000,
            }


            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )


            return response.text
        except Exception as e:
            raise Exception(f"Error generating content with Gemini: {str(e)}")


    def analyze_with_structured_output(
        self,
        prompt: str,
        output_schema: Dict[str, str],
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Analyze content and return structured JSON output


        Args:
            prompt: The analysis prompt
            output_schema: Expected output schema description
            temperature: Temperature for response generation


        Returns:
            Parsed JSON response
        """
        try:
            structured_prompt = f"""{prompt}


Please provide your response in the following JSON format:
{json.dumps(output_schema, indent=2)}


Return only valid JSON without any additional text or markdown formatting.
"""


            response_text = self.generate_content(structured_prompt, temperature)


            # Clean response - remove markdown code blocks if present
            cleaned_response = response_text.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]


            cleaned_response = cleaned_response.strip()


            # Parse JSON
            result = json.loads(cleaned_response)
            return result


        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response: {str(e)}\nResponse: {response_text}")
        except Exception as e:
            raise Exception(f"Error in structured analysis: {str(e)}")


    def batch_analyze(self, prompts: List[str], temperature: float = 0.7) -> List[str]:
        """
        Analyze multiple prompts in batch


        Args:
            prompts: List of prompts to analyze
            temperature: Temperature for response generation


        Returns:
            List of responses
        """
        responses = []
        for prompt in prompts:
            try:
                response = self.generate_content(prompt, temperature)
                responses.append(response)
            except Exception as e:
                responses.append(f"Error: {str(e)}")


        return responses


    def create_chat_session(self, session_id: str, history: Optional[List[Dict[str, str]]] = None):
        """
        Create a chat session for multi-turn conversations


        Args:
            session_id: Unique identifier for the chat session
            history: Optional conversation history
        """
        self.chat_sessions[session_id] = self.model.start_chat(history=history or [])


    def chat(self, session_id: str, message: str) -> str:
        """
        Send a message in an existing chat session


        Args:
            session_id: The chat session ID
            message: Message to send


        Returns:
            Response from Gemini
        """
        if session_id not in self.chat_sessions:
            raise ValueError(f"Chat session {session_id} not found")


        response = self.chat_sessions[session_id].send_message(message)
        return response.text



