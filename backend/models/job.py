from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from .employer import Employer
from .job_meta import JobMeta


class Base(DeclarativeBase):
    pass


class Job(Base):
    """
    This is the job model. It is used to store the job data.
    """

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    location: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    meta: Mapped["JobMeta"] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    employer: Mapped["Employer"] = relationship(
        back_populates="jobs", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Job(id={self.id}, title={self.title}, location={self.location})>"
