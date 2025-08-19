from pydantic import BaseModel, Json
from app.schemas.search import SpiderConfig, AIProviderConfig, CV
from app.schemas.job import JobAiCoverLetter, JobAiSummary


class SearchTaskResponse(BaseModel):
    id: str
    status: str


class SearchTaskRequest(BaseModel):
    spider_config: SpiderConfig
    ai_provider_config: AIProviderConfig
    ai_provider: str
    user_cv: CV


class CrawledJobResult(BaseModel):
    job_id: str
    job_title: str
    job_url: str
    job_location: str
    employer: str
    employer_url: str
    job_description: str
    seniority_level: str
    employment_type: str
    job_function: str
    industries: str
    source: str


class AIProcessedJobResult(CrawledJobResult):
    job_summary: str
    cover_letter: str
