import requests
from typing import List
from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.signalmanager import dispatcher
from celery.utils.log import get_task_logger
from app.celery_app import celery_app
from app.core.spiders.linkedin_api_spider import LinkedInSpider
from app.core.llm.google import GoogleAIProvider
from app.core.llm.ollama import OllamaProvider
from app.schemas.job import JobAiCoverLetter, JobAiSummary
from app.schemas.search import AIProviderConfig, SpiderConfig, CV
from app.schemas.task import CrawledJobResult, AIProcessedJobResult

logger = get_task_logger(__name__)


def _get_user_cv_context(user_cv: dict) -> str:
    """Get the user CV context."""
    result = ""
    result += f"Name: {user_cv.get('name')}\n"
    result += f"Title: {user_cv.get('title')}\n"
    result += f"About: {user_cv.get('about')}\n"
    result += f"Highlights: {user_cv.get('highlights')}\n"
    result += "Experience:\n"
    for experience in user_cv.get('experience', []):
        result += f"  Company: {experience.get('company')}\n"
        result += f"  Position: {experience.get('position')}\n"
        result += f"  Start Date: {experience.get('start_date')}\n"
        result += f"  End Date: {experience.get('end_date')}\n"
        result += f"  Description: {experience.get('description')}\n\n"
    result += f"Skills: {','.join(user_cv.get('skills', []))}\n"
    result += "Education:\n"
    for education in user_cv.get('education', []):
        result += f"  Title: {education.get('title')}\n"
        result += f"  Start Date: {education.get('start_date')}\n"
        result += f"  End Date: {education.get('end_date')}\n"
        result += f"  Description: {education.get('description')}\n\n"
    return result


def _get_job_context(job_data: dict) -> str:
    """Get the job context."""
    result = ""
    result += f"Title: {job_data.get('job_title')}\n"
    result += f"Company: {job_data.get('employer')}\n"
    result += f"Location: {job_data.get('job_location')}\n"
    result += f"Employment Type: {job_data.get('employment_type')}\n"
    result += f"Seniority Level: {job_data.get('seniority_level')}\n"
    result += f"Job Function: {job_data.get('job_function')}\n"
    result += f"Industries: {job_data.get('industries')}\n"
    result += f"HTML Description: {job_data.get('job_description')}\n"
    return result


def _get_system_prompt(user_cv: dict, job_data: dict) -> str:
    """Get the system prompt for the AI provider."""
    return f"""
    You are a job professional job search assistant.
    You are given a job description and a user's CV.
    Your task is to help the user with its request.
    Stricly follow the user's request.

    USER CV CONTEXT:
    {_get_user_cv_context(user_cv)}

    JOB DESCRIPTION:
    {_get_job_context(job_data)}
    """


@celery_app.task
def crawl_jobs(config: dict):
    """
    Crawl jobs from the web using Scrapy.
    """
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
    process.crawl(LinkedInSpider, **config)
    process.start()

    return jobs


@celery_app.task
def process_jobs_with_ai(jobs: List[dict], config: dict, provider: str, user_cv: dict):
    """
    Process jobs with AI agent.
    """
    processed_jobs: List[dict] = []
    conf = AIProviderConfig(**config)

    # Process each job
    for job in jobs:
        # Generate system prompt
        system_prompt = _get_system_prompt(user_cv, job)

        # Initialize AI provider based on config
        if provider.lower() == "google":
            ai_provider = GoogleAIProvider(conf, system_prompt)
        elif provider.lower() == "ollama":
            ai_provider = OllamaProvider(conf, system_prompt)
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")

        # Generate job summary using the prompt from interface
        job_summary_prompt = """
        TASK:
        Create a concise job summary that captures:
            1. Responsibilities: The key responsibilities of the role
            2. Requirements: The main requirements or qualifications
            3. Opportunity Interest: What makes this opportunity interesting or unique for the user. use personal pronouns like "you" and "your".
            4. Background Alignment: How it aligns with the candidate's background. Set level of alignment from 1 to 5.
            5. Summary: Job summary in 3-4 sentences based only on the job description.
            
        Keep it concise but informative and personalized to the candidate's profile.
        """.rstrip()

        job_summary = ai_provider.generate(job_summary_prompt, JobAiSummary)

        # Generate cover letter using the prompt from interface
        cover_letter_prompt = """
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
        """.rstrip()

        cover_letter = ai_provider.generate(
            cover_letter_prompt, JobAiCoverLetter)

        processed_jobs.append(AIProcessedJobResult(
            **job,
            job_summary=job_summary,
            cover_letter=cover_letter,
        ).model_dump(mode="json"))

    return processed_jobs


@celery_app.task
def handle_search_task(jobs: List[dict], webhook: str):
    for job in jobs:
        res = requests.post(webhook, json=AIProcessedJobResult(
            **job).model_dump(mode="json"))
        res.raise_for_status()
