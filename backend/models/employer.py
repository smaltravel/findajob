from typing import List
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from .job import Job


class Base(DeclarativeBase):
    pass


class Employer(Base):
    """
    This is the employer model. It is used to store the employer data.
    """

    __tablename__ = "employers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_ids: Mapped[List["Job"]] = mapped_column(ForeignKey("jobs.id"))
    name: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    industries: Mapped[list[str]] = mapped_column(String)

    def __repr__(self):
        return f"<Employer(id={self.id}, name={self.name})>"
