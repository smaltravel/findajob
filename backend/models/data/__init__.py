# This is the models package. It contains the models for the database.

from .employer import Employer
from .job_meta import JobMeta
from .job import Job
from .task import Task
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

# Create a unified metadata object
metadata = MetaData()


# Create a unified Base class
class Base(DeclarativeBase):
    metadata = metadata


# Export all models
__all__ = ['Base', 'Task', 'Job', 'JobMeta', 'Employer']
