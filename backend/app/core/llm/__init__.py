from abc import ABC, abstractmethod
from pydantic import BaseModel
from app.schemas.search import AIProviderConfig

class LLM(ABC):
    def __init__(self, config: AIProviderConfig, system_prompt: str = None):
        self.config = config
        self.system_prompt = system_prompt

    @abstractmethod
    def generate(self, prompt: str, format: BaseModel) -> str:
        pass
