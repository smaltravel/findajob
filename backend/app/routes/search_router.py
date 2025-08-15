from typing import List
from celery import chain
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.task import AIProcessedJobResult, SearchTaskRequest, SearchTaskResponse
from app.tasks.search import crawl_jobs, process_jobs_with_ai, handle_search_task
from app.config.database import get_db
from app.models import Job, JobMeta, Employer
from app.config.loader import settings

search_router = APIRouter(
    prefix="/search",
    tags=["Search"]
)


@search_router.post("/", response_model=SearchTaskResponse)
def search_jobs(request: SearchTaskRequest):
    webhook_url = f"{settings.WEBHOOK_BASE_URL}/api/jobs"

    # Create the task chain: crawl_jobs -> process_jobs_with_ai -> handle_search_task
    # The jobs from crawl_jobs will be passed as the last parameter to process_jobs_with_ai
    tasks_chain = (
        crawl_jobs.s(request.spider_config.model_dump(mode="json")) |
        process_jobs_with_ai.s(
            request.ai_provider_config.model_dump(mode="json"),
            request.ai_provider,
            request.user_cv.model_dump(mode="json")
        ) |
        handle_search_task.s(webhook_url)
    )
    task = tasks_chain.apply_async()
    return SearchTaskResponse(status=task.status, id=task.id)


@search_router.get("/{task_id}/status")
def get_task_status(task_id: str):
    # TODO: Implement proper task status checking
    return {"status": "unknown", "task_id": task_id}
