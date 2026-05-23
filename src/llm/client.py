"""Gemini client utilities for the LLM GridWorld agent."""
import json
import os
import re
from typing import Any
from dotenv import load_dotenv
from google import genai
from google.genai import types
from src.actions import Action

FALLBACK_ACTION = {
    "action": Action.WAIT.value,
    "reason": "Fallback action used because the model did not return a valid response.",
}

class GeminiClient:
    """Small wrapper around the Gemini API with JSON extraction and fallback logic."""

    def __init__(self, model_name: str = "gemini-3.1-flash-lite-preview", max_retries: int = 2):
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self.max_retries = max_retries

        if self.api_key is None or self.api_key.strip() == "":
            raise ValueError(
                "GEMINI_API_KEY is missing. Create a .env file and add: "
                "GEMINI_API_KEY=your_api_key_here")
        self.client = genai.Client(api_key=self.api_key)

    def generate_action(self, system_prompt: str, user_prompt: str) -> dict:
        """Ask Gemini for one action and return a parsed JSON dictionary."""
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json",
                        temperature=0.2)
                )

                response_text = self._get_response_text(response)
                parsed_response = extract_json(response_text)

                if not isinstance(parsed_response, dict):
                    raise ValueError("Model response JSON is not an object.")
                return parsed_response
            except (json.JSONDecodeError, ValueError) as error:
                last_error = error
                print(f"[GeminiClient] Invalid model response on attempt {attempt + 1}: {error}")
            except Exception as error:
                last_error = error
                print(f"[GeminiClient] Gemini request failed on attempt {attempt + 1}: {error}")
        print(f"[GeminiClient] Using fallback action after retries. Last error: {last_error}")
        return FALLBACK_ACTION.copy()

    def _get_response_text(self, response) -> str:
        """Extract text from a Gemini response object."""
        if response.text is not None and response.text.strip() != "":
            return response.text

        if not response.candidates:
            raise ValueError("Gemini returned no candidates.")

        candidate = response.candidates[0]

        if candidate.content is None or candidate.content.parts is None:
            raise ValueError("Gemini returned a candidate without content parts.")

        text_parts = []

        for part in candidate.content.parts:
            if part.text is not None:
                text_parts.append(part.text)

        response_text = "".join(text_parts).strip()

        if response_text == "":
            raise ValueError("Gemini returned an empty text response.")

        return response_text


def extract_json(text: str) -> dict[str, Any]:
    """Extract a JSON object from model output."""
    cleaned_text = text.strip()

    if cleaned_text.startswith("```"):
        cleaned_text = cleaned_text.replace("```json", "")
        cleaned_text = cleaned_text.replace("```JSON", "")
        cleaned_text = cleaned_text.replace("```", "")
        cleaned_text = cleaned_text.strip()

    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned_text, re.DOTALL)
        if match is None:
            raise ValueError("No JSON object found in the model response.")
        json_text = match.group(0)
        return json.loads(json_text)