from .interface import AIProvider, AIProviderConfig, AIProviderError
from ollama import Client
from pydantic import BaseModel
import json
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class OllamaProvider(AIProvider):
    """Ollama AI provider implementation with CV and job context management."""

    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        self.__client = Client(host=self.config.base_url)

        # Conversation history for maintaining context
        self.__conversation_history: List[Dict] = []

    def _generate(self, prompt: str, format: BaseModel) -> str:
        """
        Generate text using Ollama API.
        """

        for resp in self.__client.list():
            if not any([m.model == self.config.model for m in resp[1]]):
                raise AIProviderError(f"Model {self.config.model} not found")

        response = self.__client.generate(
            model=self.config.model,
            system=self._get_system_prompt(),
            prompt=prompt,
            format=format.model_json_schema(),
        )

        return format.model_validate_json(response.response).model_dump_json()
