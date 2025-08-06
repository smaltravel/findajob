#!/usr/bin/env python3
"""
AI Providers Interface
"""

from abc import ABC, abstractmethod
from typing import Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AIProviderConfig:
    """Configuration for AI providers."""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = "default"
    timeout: int = 120
    temperature: float = 0.7
    user_cv: Optional[dict] = None
    job: Optional[dict] = None


class AIProviderError(Exception):
    """Base exception for AI provider errors."""
    pass


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    def __init__(self, config: AIProviderConfig):
        """
        Initialize the AI provider.

        Args:
            config: Configuration for the AI provider
        """
        self.config = config

    def set_user_cv(self, user_cv: dict):
        """
        Set the user's CV data.
        """
        self.config.user_cv = user_cv

    def set_job(self, job: dict):
        """
        Set the job data.
        """
        self.config.job = job

    @abstractmethod
    def job_description(self, **kwargs) -> str:
        """
        Generate a job description using the AI provider.
        """
        pass

    @abstractmethod
    def cover_letter(self, **kwargs) -> str:
        """
        Generate a cover letter using the AI provider.
        """
        pass
