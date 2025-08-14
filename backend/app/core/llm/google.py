from . import LLM
from google import genai
from pydantic import BaseModel
from app.schemas.search import AIProviderConfig


class GoogleAIProvider(LLM):
    """Google AI provider implementation with CV and job context management."""

    def __init__(self, config: AIProviderConfig, system_prompt: str = None):
        super().__init__(config, system_prompt)

        if not self.config.api_key:
            raise ValueError("Google AI API key is required")

        self.__client = genai.Client(
            api_key=self.config.api_key,
        )

    def generate(self, prompt: str, format: BaseModel) -> str:
        """Generate text using Google AI API."""

        response = self.__client.models.generate_content(
            model=self.config.model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                temperature=self.config.temperature,
                system_instruction=[l for l in self.system_prompt.split(
                    "\n") if len(l.strip()) > 0],
                response_schema=format.model_json_schema(),
                response_mime_type='application/json',
            )
        )

        return format.model_validate_json(response.text).model_dump_json()
