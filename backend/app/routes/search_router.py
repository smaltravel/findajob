from typing import List
from celery import chain
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.schemas.task import AIProcessedJobResult, SearchTaskRequest, SearchTaskResponse
from app.tasks.search import crawl_jobs, process_jobs_with_ai, handle_search_task
from backend.app.config.database import get_db

search_router = APIRouter(
    prefix="/search",
    tags=["Search"]
)


@search_router.post("/", response_model=SearchTaskResponse)
def search_jobs(request: Request, task_request: SearchTaskRequest):
    webhook_url = f"{request.base_url}/search/complete"
    tasks_chain = crawl_jobs.s(task_request.spider_config) | process_jobs_with_ai.s(
        request.ai_provider_config, task_request.ai_provider, task_request.user_cv) | handle_search_task.s(webhook_url)
    task = tasks_chain.apply_async()
    return SearchTaskResponse(status=task.status, id=task.id)


@search_router.get("/{task_id}/status")
def get_task_status(task_id: str):
    status = get_task_status(task_id)
    return status


@search_router.post("/complete")
def handle_search_task_complete(jobs: List[AIProcessedJobResult], db: Session = Depends(get_db)):
    for job in jobs:
        db.add(job)
    db.commit()
