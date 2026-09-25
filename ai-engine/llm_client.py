import json
from typing import Any

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL


class GeminiClient:
    def __init__(self) -> None:
        self.client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        self.model = GEMINI_MODEL

    def generate_text(
        self,
        prompt: str,
    ) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2
            )
        )

        if not response.text:
            raise ValueError(
                "Gemini returned an empty response."
            )

        return response.text

    def generate_json(
        self,
        prompt: str,
    ) -> dict[str, Any]:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json"
            )
        )

        if not response.text:
            raise ValueError(
                "Gemini returned an empty response."
            )

        try:
            parsed_response = json.loads(
                response.text
            )
        except json.JSONDecodeError as error:
            raise ValueError(
                "Gemini returned malformed JSON."
            ) from error

        if not isinstance(parsed_response, dict):
            raise ValueError(
                "Gemini response must be a JSON object."
            )

        return parsed_response