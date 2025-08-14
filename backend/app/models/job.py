from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models import Base
from app.models.employer import Employer
from app.models.job_meta import JobMeta
from app.models.task import Task


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
    task: Mapped["Task"] = relationship("Task", back_populates="jobs")
    meta: Mapped["JobMeta"] = relationship(
        "JobMeta", back_populates="job", uselist=False, cascade="all, delete-orphan")
    employer: Mapped["Employer"] = relationship(
        "Employer", back_populates="job", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Job(id={self.id}, title={self.title}, location={self.location})>"
