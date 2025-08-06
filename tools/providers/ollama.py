from .interface import AIProvider, AIProviderConfig, AIProviderError
from ollama import Client
from pydantic import BaseModel
import json
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class JobSummary(BaseModel):
    responsibilities: str
    requirements: List[str]
    opportunity_interest: str
    background_aligns: str
    summary: str


class CoverLetter(BaseModel):
    subject: str
    letter_content: str
    letter_closing: str


def handle_raise(func):
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except AIProviderError as e:
            raise e
        except Exception as e:
            raise AIProviderError(f"Error in {func.__name__}: {e}")
    return wrapper


class OllamaProvider(AIProvider):
    """Ollama AI provider implementation with CV and job context management."""

    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        self.__client = Client(host=self.config.base_url)

        # Conversation history for maintaining context
        self.__conversation_history: List[Dict] = []

    def __get_user_cv_context(self) -> str:
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

    def __get_job_context(self) -> str:
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

    def __system_prompt(self) -> str:
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
        {self.__get_user_cv_context()}

        JOB DESCRIPTION:
        {self.__get_job_context()}
        """

    def __generate(self, prompt: str, format: BaseModel) -> str:
        """
        Generate text using Ollama API.
        """

        for resp in self.__client.list():
            if not any([m.model == self.config.model for m in resp[1]]):
                raise AIProviderError(f"Model {self.config.model} not found")

        response = self.__client.generate(
            model=self.config.model,
            system=self.__system_prompt(),
            prompt=prompt,
            format=format.model_json_schema(),
        )

        return format.model_validate_json(response.response).model_dump_json()

    @handle_raise
    def job_description(self, **kwargs) -> str:
        """
        Generate a job description using the AI provider.
        """
        prompt = """
        TASK:
        Create a concise job summary that captures:
            1. The key responsibilities of the role
            2. The main requirements or qualifications
            3. What makes this opportunity interesting or unique
            4. How it aligns with the candidate's background. Set level of alignment from 1 to 5.
            5. Job summary in 3-4 sentences
            
        Keep it concise but informative and personalized to the candidate's profile.
        """
        return self.__generate(prompt, JobSummary)

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
        return self.__generate(prompt, CoverLetter)
