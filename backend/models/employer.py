from typing import List
from sqlalchemy import ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from . import Base
from .job import Job


class Employer(Base):
    """
    This is the employer model. It is used to store the employer data.
    """

    __tablename__ = "employers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    jobs: Mapped[List["Job"]] = mapped_column(ForeignKey("jobs.id"))
    name: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    industries: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Employer(id={self.id}, name={self.name})>"
