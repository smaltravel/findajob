import requests
import json
from typing import Dict, List
from datetime import datetime
from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.signalmanager import dispatcher
from celery.utils.log import get_task_logger
from google.genai.types import FunctionDeclaration, Tool
from app.celery_app import celery_app
from app.core.spiders.linkedin_api_spider import LinkedInSpider
from app.core.llm.google import GoogleAIProvider
from app.core.llm.ollama import OllamaProvider
from app.schemas.job import AlignmentScore, JobAiCoverLetter, JobAiSummary
from app.schemas.search import AIProviderConfig, LanguageProficiency, SpiderConfig, CV
from app.schemas.task import AIProcessedJobResult

logger = get_task_logger(__name__)


def calculate_month_between(start_date: str, end_date: str) -> int:
    """
    Calculate the number of months between two dates in YYYY-MM format.

    Args:
        start_date (str): Start date in YYYY-MM format (e.g., "2020-01")
        end_date (str): End date in YYYY-MM format (e.g., "2023-06")

    Returns:
        int: Number of months between the dates
    """
    try:
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m")
        end = datetime.strptime(end_date, "%Y-%m")

        # Calculate months difference
        return (end.year - start.year) * 12 + (end.month - start.month)

    except ValueError as e:
        raise ValueError(
            f"Invalid date format. Expected YYYY-MM, got: {start_date} and {end_date}") from e


def calculate_skills_score(candidate_skills: List[str], job_skills: List[str]) -> int:
    """
    Calculate the alignment score between a candidate skills and job required skills.
    """
    score = 0
    for skill in job_skills:
        if skill in candidate_skills:
            score += 1
    return score / len(job_skills) * 100


def calculate_experience_score(candidate_experience: float, job_experience: float) -> int:
    """
    Calculate the alignment score between a candidate experience and job required experience.
    """
    return candidate_experience / job_experience * 100 if candidate_experience < job_experience else 100


def calculate_industries_score(candidate_industries: List[str], job_industries: List[str]) -> int:
    """
    Calculate the alignment score between a candidate industries and job required industries.
    """
    score = 0
    for industry in job_industries:
        if industry in candidate_industries:
            score += 1

    return score / len(job_industries) * 100


def calculate_languages_score(candidate_languages: Dict[str, LanguageProficiency],
                              job_languages: Dict[str, LanguageProficiency]) -> int:
    """
    Calculate the alignment score between a candidate languages and job required languages.
    """
    diffs: list[int] = []

    for language in candidate_languages.keys() & job_languages.keys():
        diffs.append(
            100 - abs(candidate_languages[language] - job_languages[language]))

    return sum(diffs) / len(job_languages.keys()) if len(job_languages.keys()) > 0 else 100


def calculate_overall_score(scores: AlignmentScore) -> int:
    """
    Calculate the overall score based on the parts.
    """
    weights = {
        "skills": 0.3,
        "education": 0.1,
        "experience": 0.3,
        "location": 0.05,
        "industries": 0.05,
        "languages": 0.2
    }

    return sum(weights[key] * scores[key] for key in weights)


calculate_month_between_function = FunctionDeclaration(
    name="calculate_month_between",
    description="Calculate the number of months between two dates in YYYY-MM format.",
    parameters_json_schema={
        "type": "object",
        "properties": {
            "start_date": {
                "type": "string",
                "description": "Start date in YYYY-MM format"
            },
            "end_date": {
                "type": "string",
                "description": "End date in YYYY-MM format"
            }
        },
        "required": ["start_date", "end_date"]
    },
    response_json_schema={
        "type": "integer",
        "description": "Number of months between the dates"
    }
)

calculate_overall_score_function = FunctionDeclaration(
    name="calculate_overall_score",
    description="Calculate the overall score based on the parts.",
    parameters_json_schema={
        "type": "object",
        "properties": {
            "scores": {
                "type": "object",
                "properties": {
                    "skills": {
                        "type": "integer"
                    },
                    "education": {
                        "type": "integer"
                    },
                    "experience": {
                        "type": "integer"
                    },
                    "location": {
                        "type": "integer"
                    },
                    "industries": {
                        "type": "integer"
                    }
                }
            }
        },
        "required": ["scores"]
    },
    response_json_schema={
        "type": "integer",
        "description": "Overall score"
    }
)
calculate_industries_score_function = FunctionDeclaration(
    name="calculate_industries_score",
    description="Calculate the alignment score between a candidate industries and job required industries.",
    parameters_json_schema={
        "type": "object",
        "properties": {
            "candidate_industries": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "job_industries": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            }
        },
        "required": ["candidate_industries", "job_industries"]
    },
    response_json_schema={
        "type": "integer",
        "description": "Alignment score between a candidate industries and job required industries"
    }
)
calculate_skills_score_function = FunctionDeclaration(
    name="calculate_skills_score",
    description="Calculate the alignment score between a candidate skills and job required skills.",
    parameters_json_schema={
        "type": "object",
        "properties": {
            "candidate_skills": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "job_skills": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            }
        },
        "required": ["candidate_skills", "job_skills"]
    },
    response_json_schema={
        "type": "integer",
        "description": "Alignment score between a candidate skills and job required skills"
    }
)
calculate_experience_score_function = FunctionDeclaration(
    name="calculate_experience_score",
    description="Calculate the alignment score between a candidate experience and job required experience.",
    parameters_json_schema={
        "type": "object",
        "properties": {
            "candidate_experience": {
                "type": "integer",
                "description": "Candidate experience in months"
            },
            "job_experience": {
                "type": "integer",
                "description": "Job experience in months"
            }
        },
        "required": ["candidate_experience", "job_experience"]
    },
    response_json_schema={
        "type": "integer",
        "description": "Alignment score between a candidate experience and job required experience"
    }
)
calculate_languages_score_function = FunctionDeclaration(
    name="calculate_languages_score",
    description="Calculate the alignment score between a candidate languages and job required languages.",
    parameters_json_schema={
        "type": "object",
        "properties": {
            "candidate_languages": {
                "type": "object",
                "properties": {
                    "languages": {
                        "additionalProperties": {
                            "enum": [0, 15, 30, 45, 60, 75, 90, 100],
                            "title": "LanguageProficiency",
                            "type": "integer"
                        },
                        "description": "Languages spoken by the person",
                        "title": "Languages",
                        "type": "object"
                    }
                }
            },
            "job_languages": {
                "type": "object",
                "properties": {
                    "languages": {
                        "additionalProperties": {
                            "enum": [0, 15, 30, 45, 60, 75, 90, 100],
                            "title": "LanguageProficiency",
                            "type": "integer"
                        },
                        "description": "Languages spoken by the person",
                        "title": "Languages",
                        "type": "object"
                    }
                }
            }
        },
        "required": ["candidate_languages", "job_languages"]
    },
    response_json_schema={
        "type": "integer",
        "description": "Alignment score between a candidate languages and job required languages"
    }
)
tools = [
    Tool(function_declarations=[calculate_month_between_function]),
    Tool(function_declarations=[calculate_overall_score_function]),
    Tool(function_declarations=[calculate_skills_score_function]),
    Tool(function_declarations=[calculate_experience_score_function]),
    Tool(function_declarations=[calculate_industries_score_function]),
    Tool(function_declarations=[calculate_languages_score_function]),
]
callable_tools = {
    "calculate_month_between": calculate_month_between,
    "calculate_overall_score": calculate_overall_score,
    "calculate_skills_score": calculate_skills_score,
    "calculate_experience_score": calculate_experience_score,
    "calculate_industries_score": calculate_industries_score,
    "calculate_languages_score": calculate_languages_score,
}


class SearchPipeline:
    def __init__(self, spider_config: dict, ai_config: dict, provider: str, user_cv: dict, webhook: str):
        self.spider_config: SpiderConfig = SpiderConfig.model_validate(
            spider_config)
        self.ai_config: AIProviderConfig = AIProviderConfig.model_validate(
            ai_config)
        self.user_cv: CV = CV.model_validate(user_cv)

        self.webhook = webhook

        # Initialize AI provider based on config
        if provider.lower() == "google":
            self.provider = GoogleAIProvider(self.ai_config, logger)
        elif provider.lower() == "ollama":
            self.provider = OllamaProvider(self.ai_config, logger)
        else:
            raise ValueError(
                f"Unsupported AI provider: {provider}")
        self.provider.system_prompt = self._get_system_prompt()
        self.provider.tools = tools
        self.provider.callable_tools = callable_tools

    def run(self) -> None:
        jobs: List[dict] = []

        for job in self._crawl():
            self.provider.clear_history()
            jobs.append(self._process_job_with_ai(job))

        self._handle_search_task(jobs)

    def _get_user_cv_context(self) -> str:
        """Get the user CV context."""
        return self.user_cv.model_dump_json()

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AI provider."""
        return f"""You are an expert job search assistant helping a candidate evaluate and apply for jobs.

NORMALIZED CANDIDATE PROFILE JSON: {self._get_user_cv_context()}

INSTRUCTIONS:
- Provide personalized, specific advice based on the candidate's background
- Focus on actionable insights and concrete examples
- Maintain professional but warm tone
- Be concise and structured in responses
"""

    def _crawl(self):
        """Crawl jobs from the web using Scrapy."""
        jobs: List[dict] = []

        def crawler_results(signal, sender, item, response, spider):
            jobs.append(item)

        dispatcher.connect(crawler_results, signal=signals.item_scraped)

        process = CrawlerProcess(settings={
            "LOG_LEVEL": "INFO",
            "BOT_NAME": "findajob",
            "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
            "DOWNLOAD_DELAY": 1,
            "FEED_EXPORT_ENCODING": "utf-8",
            "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            "DOWNLOAD_HANDLERS": {
                "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
                "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            },
            "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        })
        process.crawl(LinkedInSpider, **
                      self.spider_config.model_dump(mode="json"))
        process.start()

        return jobs

    def _process_job_with_ai(self, job: dict):
        """Process jobs with AI agent."""

        # Generate job summary using the prompt from interface
        job_summary_prompt = f"""TASK: Create a concise job summary that captures:

1. Responsibilities (3-5 key points):
   - Extract the most important responsibilities from the job description
   - Focus on what the role actually does day-to-day

2. Requirements (3-5 key points):
   - List essential qualifications and skills
   - Distinguish between "must-have" and "nice-to-have" requirements

3. Opportunity Interest (2-3 sentences):
   - What makes this role exciting for YOU specifically
   - Use personal pronouns and connect to your career goals
   - Highlight unique aspects of the company/role
   - Based on the overall score, provide a recommendation to the candidate if they should apply for the job or not

4. Background Alignment Score (0-100 scale):
   - Calculate the alignment score based on the candidate profile and job requirements
   - Use candidate profile from the system prompt
   - Normalize job requirements, skills, education, experience, location, industries, languages to calculate the alignment score
   - All normalized values must be lowercase
   - Normalize languages by the following rules:
     - Format: language: proficiency
     - Proficiency: a1 -> 15; a2 -> 30; b1 -> 45; b2 -> 60; c1 -> 75; c2 -> 90; native -> 100
     - Do not use not required languages in the job requirements in the calculate_languages_score tool
   - To calculate experience score, use the calculate_month_between tool
   - To calculate skills score, use the calculate_skills_score tool
   - To calculate industries score, use the calculate_industries_score tool
   - To calculate location see distance between candidate location and job location and its willingness to relocate or available to work remotely
   - To calculate education score, lexigraphic comparison of candidate's education and employer's requirement. If it matches, score is 100, if it near match, score is 50, if it doesn't match, score is 0.
   - To calculate overall score, use the calculate_overall_score tool
   - To calculate languages score, use the calculate_languages_score tool

5. Summary (3-4 sentences):
   - Concise overview of the role and why it's a good fit
   - Focus on the most compelling aspects for your profile

JSON JOB DATA: {json.dumps(job)}

Keep responses concise, specific, and personalized to the candidate's background.
"""

        job_summary = self.provider.agent(
            job_summary_prompt, JobAiSummary)

        # Generate cover letter using the prompt from interface
        cover_letter_prompt = """TASK: Create a compelling, personalized cover letter that:

**Structure & Format:**
- Professional greeting (avoid "To Whom It May Concern")
- Opening paragraph: Express interest and connection to the role
- Body paragraphs (2-3): Highlight relevant experience and skills
- Closing: Strong call-to-action and professional sign-off

**Content Requirements:**
1. **Opening Hook**: Start with why you're excited about this specific role/company
2. **Experience Alignment**: Connect 2-3 specific experiences from your CV to job requirements
3. **Skill Demonstration**: Show how your skills directly address their needs
4. **Company Knowledge**: Demonstrate understanding of their business/industry
5. **Cultural Fit**: Explain why you'd thrive in their environment
6. **Closing**: Express enthusiasm and request next steps

**Tone & Style:**
- Professional but warm and engaging
- Confident but not arrogant
- Specific and concrete examples
- 250-350 words maximum
- Use active voice and strong action verbs

Make it personal, specific to this opportunity, and compelling based on your actual CV data.
"""

        cover_letter = self.provider.generate(
            cover_letter_prompt, JobAiCoverLetter)

        return AIProcessedJobResult(
            **job,
            job_summary=job_summary,
            cover_letter=cover_letter,
        ).model_dump(mode="json")

    def _handle_search_task(self, jobs: List[dict]):
        for job in jobs:
            res = requests.post(self.webhook, json=AIProcessedJobResult(
                **job).model_dump(mode="json"))
            res.raise_for_status()


@celery_app.task
def run_search_pipeline(spider_config: dict, ai_config: dict, provider: str, user_cv: dict, webhook: str) -> None:
    pipeline = SearchPipeline(
        spider_config=spider_config,
        ai_config=ai_config,
        provider=provider,
        user_cv=user_cv,
        webhook=webhook
    )
    pipeline.run()
