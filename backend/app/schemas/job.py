from typing import List
from pydantic import BaseModel, HttpUrl
from app.schemas.employer import Employer


class AlignmentScore(BaseModel):
    """Alignment score between a candidate profile and job requirements."""
    total: int
    skills: int
    education: int
    experience: int
    location: int
    industries: int
    languages: int


class JobAiSummary(BaseModel):
    responsibilities: List[str]
    requirements: List[str]
    opportunity_interest: str
    background_aligns: AlignmentScore
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
    ai_metadata: JobAiSummary
    cover_letter: JobAiCoverLetter


class Job(BaseModel):
    id: int
    title: str
    location: str
    url: HttpUrl
    status: str
    source: str
    meta: JobMeta
    employer: Employer
