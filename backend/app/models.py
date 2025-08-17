import datetime
from typing import List
from sqlalchemy import Integer, String, ForeignKey, JSON, DateTime, MetaData
from sqlalchemy.orm import Mapped, DeclarativeBase, mapped_column, relationship
from sqlalchemy.sql import func
from app.schemas.job import JobAiSummary, JobAiCoverLetter

# Create a unified metadata object
metadata = MetaData()

# Create a unified Base class


class Base(DeclarativeBase):
    metadata = metadata


class Employer(Base):
    """
    This is the employer model. It is used to store the employer data.
    """

    __tablename__ = "employers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    industries: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now())

    # Use relationship instead of ForeignKey for the jobs
    jobs: Mapped[List["Job"]] = relationship("Job", back_populates="employer")

    def __repr__(self):
        return f"<Employer(id={self.id}, name={self.name})>"


class JobMeta(Base):
    """
    This is the job meta model. It is used to store the job meta data.
    """

    __tablename__ = "job_meta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey(
        "jobs.id"), nullable=False)  # Fixed: job_id not jobs
    job_description: Mapped[str] = mapped_column(String)
    employment_type: Mapped[str] = mapped_column(String)
    job_function: Mapped[str] = mapped_column(String)
    seniority_level: Mapped[str] = mapped_column(String)
    ai_metadata: Mapped[JobAiSummary] = mapped_column(JSON, nullable=True)
    cover_letter: Mapped[JobAiCoverLetter] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now())

    # Add relationship back to Job
    job: Mapped["Job"] = relationship("Job", back_populates="meta")

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
    status: Mapped[str] = mapped_column(String, default="new")
    source: Mapped[str] = mapped_column(String, default="unknown")
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("employers.id"), nullable=False)

    # Use string references for relationships to avoid circular imports
    meta: Mapped["JobMeta"] = relationship(
        "JobMeta", back_populates="job", uselist=False)
    employer: Mapped["Employer"] = relationship(
        "Employer", back_populates="jobs")

    def __repr__(self):
        return f"<Job(id={self.id}, title={self.title}, location={self.location})>"
