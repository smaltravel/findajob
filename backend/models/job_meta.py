from sqlalchemy import ForeignKey, Integer, String, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from .job import Job


class Base(DeclarativeBase):
    pass


class JobMeta(Base):
    """
    This is the job meta model. It is used to store the job meta data.
    """

    __tablename__ = "job_meta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped["Job"] = mapped_column(ForeignKey("jobs.id"))
    job_description: Mapped[str] = mapped_column(String)
    employment_type: Mapped[str] = mapped_column(String)
    job_function: Mapped[str] = mapped_column(String)
    seniority_level: Mapped[str] = mapped_column(String)
    industries: Mapped[list[str]] = mapped_column(String)
    ai_metadata: Mapped[dict] = mapped_column(JSONB)
    cover_letter: Mapped[dict] = mapped_column(JSONB)

    def __repr__(self):
        return f"<JobMeta(id={self.id}, job_id={self.job_id})>"
