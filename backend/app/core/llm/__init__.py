from abc import ABC, abstractmethod
from logging import Logger
from typing import Callable, List, Optional
from google.genai.types import Tool
from pydantic import BaseModel
from app.schemas.search import AIProviderConfig


class LLM(ABC):
    def __init__(self, config: AIProviderConfig, logger: Logger):
        self.config = config
        self.logger = logger
        self.system_prompt: Optional[str] = None
        self.tools: Optional[List[Tool]] = None
        self.callable_tools: Optional[dict[str, Callable]] = None

    @abstractmethod
    def clear_history(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def generate(self, prompt: str, format: BaseModel) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def agent(self, prompt: str, format: BaseModel) -> Optional[str]:
        raise NotImplementedError
