# This is the models package. It contains the models for the database.

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

from app.models.employer import Employer
from app.models.job_meta import JobMeta
from app.models.job import Job
from app.models.task import Task  # noqa: F401

# Create a unified metadata object
metadata = MetaData()


# Create a unified Base class
class Base(DeclarativeBase):
    metadata = metadata


# Export all models
__all__ = ['Base', 'Task', 'Job', 'JobMeta', 'Employer']
