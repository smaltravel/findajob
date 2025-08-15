from typing import List
from pydantic import BaseModel
from sqlalchemy import Integer, String, ForeignKey, JSONB, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models import Base
from app.models.employer import Employer
from datetime import datetime


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


class JobMeta(Base):
    """
    This is the job meta model. It is used to store the job meta data.
    """

    __tablename__ = "job_meta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    jobs: Mapped["Job"] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    job_description: Mapped[str] = mapped_column(String)
    employment_type: Mapped[str] = mapped_column(String)
    job_function: Mapped[str] = mapped_column(String)
    seniority_level: Mapped[str] = mapped_column(String)
    industries: Mapped[str] = mapped_column(String)
    ai_metadata: Mapped[JobSummary] = mapped_column(JSONB, nullable=True)
    cover_letter: Mapped[CoverLetter] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<JobMeta(id={self.id}, job_id={self.job_id})>"


class Job(Base):
    """
    This is the job model. It is used to store the job data.
    """

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[str] = mapped_column(String, unique=True)
    title: Mapped[str] = mapped_column(String)
    location: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    meta: Mapped["JobMeta"] = relationship("JobMeta")
    employer: Mapped["Employer"] = relationship("Employer")

    def __repr__(self):
        return f"<Job(id={self.id}, title={self.title}, location={self.location})>"
