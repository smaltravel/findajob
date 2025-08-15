from typing import List
from pydantic import BaseModel, Field


class SpiderConfig(BaseModel):
    keywords: str
    location: str
    max_jobs: int
    seniority: int


class AIProviderConfig(BaseModel):
    model: str
    base_url: str
    api_key: str


class Experience(BaseModel):
    """Experience entry in CV."""
    company: str = Field(..., description="Company name")
    position: str = Field(..., description="Job position/title")
    start_date: str = Field(...,
                            description="Start date (format: YYYY or YYYY-MM)")
    end_date: str = Field(...,
                          description="End date (format: YYYY or YYYY-MM or 'Present')")
    description: str = Field(...,
                             description="Job description and responsibilities")


class Education(BaseModel):
    """Education entry in CV."""
    title: str = Field(..., description="Degree or certificate title")
    start_date: str = Field(..., description="Start date (format: YYYY)")
    end_date: str = Field(..., description="End date (format: YYYY)")
    description: str = Field(...,
                             description="Additional details about the education")


class CV(BaseModel):
    """Complete CV schema."""
    name: str = Field(..., description="Full name of the person")
    title: str = Field(..., description="Professional title or headline")
    about: str = Field(...,
                       description="Professional summary and about section")
    highlights: List[str] = Field(...,
                                  description="Key achievements and highlights")
    experience: List[Experience] = Field(...,
                                         description="Work experience entries")
    skills: List[str] = Field(..., description="Technical and soft skills")
    education: List[Education] = Field(...,
                                       description="Educational background")
