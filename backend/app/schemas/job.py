from typing import List
from pydantic import BaseModel, HttpUrl
from app.schemas.employer import Employer


class JobAiSummary(BaseModel):
    responsibilities: List[str]
    requirements: List[str]
    opportunity_interest: str
    background_aligns: int
    summary: str


class JobAiCoverLetter(BaseModel):
    subject: str
    letter_content: str


class JobAiMetadata(BaseModel):
    job_summary: JobAiSummary
    cover_letter: JobAiCoverLetter


class JobMeta(BaseModel):
    job_description: str
    seniority_level: str
    employment_type: str
    job_function: str
    ai_metadata: JobAiMetadata


class Job(BaseModel):
    id: int
    title: str
    location: str
    url: HttpUrl
    meta: JobMeta
    employer: Employer
