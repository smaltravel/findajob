from . import LLM
from ollama import Client
from pydantic import BaseModel
from typing import Dict, List
from app.schemas.search import AIProviderConfig


class OllamaProvider(LLM):
    """Ollama AI provider implementation with CV and job context management."""

    def __init__(self, config: AIProviderConfig, system_prompt: str = None):
        super().__init__(config, system_prompt)
        self.__client = Client(host=self.config.base_url)

    def generate(self, prompt: str, format: BaseModel) -> str:
        """
        Generate text using Ollama API.
        """

        for resp in self.__client.list():
            if not any([m.model == self.config.model for m in resp[1]]):
                raise ValueError(f"Model {self.config.model} not found")

        response = self.__client.generate(
            model=self.config.model,
            system=self.system_prompt,
            prompt=prompt,
            format=format.model_json_schema(),
        )

        return format.model_validate_json(response.response).model_dump_json()
