# FastAPI data models

from pydantic import BaseModel
from typing import Dict, Any, Optional

class PipelineResponse(BaseModel):
    run_id: str
    webhook_url: str
    status: str


class TaskData(BaseModel):
    run_id: str
    jobs_processed: int
    total_jobs: int
    status: str


class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: Dict[str, Any] = None
    error: str = None


class PipelineTask(BaseModel):
    run_id: str
    pipeline_task_id: str
    service1_task_id: str = None
    service2_task_id: str = None
    status: str = "started"


class AIProviderConfig(BaseModel):
    provider: str
    model: str
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    api_params: Optional[dict] = None


class PipelineConfig(BaseModel):
    keywords: str = "python developer"
    location: str = "remote"
    max_jobs: int = 10
    seniority: int = 3
    ai_provider_config: AIProviderConfig


class JobStatusUpdate(BaseModel):
    status: str


class JobDelete(BaseModel):
    job_id: int


__all__ = [
    "PipelineResponse",
    "TaskData",
    "TaskStatus",
    "PipelineTask",
    "AIProviderConfig",
    "PipelineConfig",
    "JobStatusUpdate",
    "JobDelete",
]