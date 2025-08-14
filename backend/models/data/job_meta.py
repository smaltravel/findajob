from sqlalchemy import ForeignKey, Integer, String, JSONB, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from . import Base
from .job import Job


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
    ai_metadata: Mapped[dict] = mapped_column(JSONB, nullable=True)
    cover_letter: Mapped[dict] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<JobMeta(id={self.id}, job_id={self.job_id})>"
