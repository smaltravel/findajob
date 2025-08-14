#!/usr/bin/env python3
"""
AI Providers Interface
"""

from abc import ABC, abstractmethod
from typing import Optional, List
import logging
from dataclasses import dataclass
from pydantic import BaseModel

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


class JobSummary(BaseModel):
    """Shared data model for job summary responses."""
    responsibilities: List[str]
    requirements: List[str]
    opportunity_interest: str
    background_aligns: int
    summary: str


class CoverLetter(BaseModel):
    """Shared data model for cover letter responses."""
    subject: str
    letter_content: str
    letter_closing: str


def handle_raise(func):
    """Shared decorator for error handling."""

    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except AIProviderError as e:
            raise e
        except Exception as e:
            raise AIProviderError(f"Error in {func.__name__}: {e}")
    return wrapper


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

    def _get_user_cv_context(self) -> str:
        """
        Get the user CV context.
        """
        result = ""
        result += f"Name: {self.config.user_cv.get('name')}\n"
        result += f"Title: {self.config.user_cv.get('title')}\n"
        result += f"About: {self.config.user_cv.get('about')}\n"
        result += f"Highlights: {self.config.user_cv.get('highlights')}\n"
        result += "Experience:\n"
        for experience in self.config.user_cv.get('experience'):
            result += f"  Company: {experience.get('company')}\n"
            result += f"  Position: {experience.get('position')}\n"
            result += f"  Start Date: {experience.get('start_date')}\n"
            result += f"  End Date: {experience.get('end_date')}\n"
            result += f"  Description: {experience.get('description')}\n\n"
        result += f"Skills: {','.join(self.config.user_cv.get('skills'))}\n"
        result += "Education:\n"
        for education in self.config.user_cv.get('education'):
            result += f"  Title: {education.get('title')}\n"
            result += f"  Start Date: {education.get('start_date')}\n"
            result += f"  End Date: {education.get('end_date')}\n"
            result += f"  Description: {education.get('description')}\n\n"
        return result

    def _get_job_context(self) -> str:
        """
        Get the job context.
        """
        result = ""
        result += f"Title: {self.config.job.get('job_title')}\n"
        result += f"Company: {self.config.job.get('employer')}\n"
        result += f"Location: {self.config.job.get('job_location')}\n"
        result += f"Employment Type: {self.config.job.get('employment_type')}\n"
        result += f"Seniority Level: {self.config.job.get('seniority_level')}\n"
        result += f"Job Function: {self.config.job.get('job_function')}\n"
        result += f"Industries: {self.config.job.get('industries')}\n"
        result += f"HTML Description: {self.config.job.get('job_description')}\n"
        return result

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the AI provider.
        """
        if not self.config.user_cv:
            raise AIProviderError(
                "CV context not set. Please set CV context first.")

        if not self.config.job:
            raise AIProviderError(
                "Job context not set. Please set job context first.")

        return f"""
        You are a job professional job search assistant.
        You are given a job description and a user's CV.
        Your task is to help the user with its request.
        Stricly follow the user's request.

        USER CV CONTEXT:
        {self._get_user_cv_context()}

        JOB DESCRIPTION:
        {self._get_job_context()}
        """

    @abstractmethod
    def _generate(self, prompt: str, format: BaseModel) -> str:
        """
        Generate text using the AI provider.
        This method must be implemented by each provider.
        """
        pass

    @handle_raise
    def job_description(self, **kwargs) -> str:
        """
        Generate a job description using the AI provider.
        """
        prompt = """
        TASK:
        Create a concise job summary that captures:
            1. Responsibilities: The key responsibilities of the role
            2. Requirements: The main requirements or qualifications
            3. Opportunity Interest: What makes this opportunity interesting or unique for the user. use personal pronouns like "you" and "your".
            4. Background Alignment: How it aligns with the candidate's background. Set level of alignment from 1 to 5.
            5. Summary: Job summary in 3-4 sentences based only on the job description.
            
        Keep it concise but informative and personalized to the candidate's profile.
        """
        return self._generate(prompt, JobSummary)

    @handle_raise
    def cover_letter(self, **kwargs) -> str:
        """
        Generate a cover letter using the AI provider.
        """
        prompt = """
        TASK:
        Create a compelling, personalized cover letter that:
            1. Addresses the hiring manager professionally
            2. Explains why the candidate is interested in this specific role and company
            3. Highlights relevant skills and experience from their CV that match the job requirements
            4. Demonstrates understanding of the company and role
            5. Shows how their background aligns with the position
            6. Includes a strong closing statement
            7. Is humanized, well-composed, and personalized based on the CV data
            
        Make it personal, specific to this opportunity, and compelling. 
        Use the candidate's actual experience and skills from their CV.
        Write in a professional but engaging tone.
        The letter should be no longer than 400 words. Optimal length is 200-350 words.
        """
        return self._generate(prompt, CoverLetter)
