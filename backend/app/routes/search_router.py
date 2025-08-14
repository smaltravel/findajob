import uuid
from celery import chain
from fastapi import APIRouter

from app.schemas.task import SearchTaskRequest, SearchTaskResponse
from app.tasks.crawling import crawl_jobs
from app.tasks.ai_agent import process_jobs_with_ai
from app.tasks import get_task_status

search_router = APIRouter(
    prefix="/search",
    tags=["Search"]
)

@search_router.post("/", response_model=SearchTaskResponse)
def search_jobs(request: SearchTaskRequest):
    run_id = str(uuid.uuid4())
    task = chain(
        crawl_jobs.s(request.spider_config, run_id),
        process_jobs_with_ai.s(request.ai_provider_config, run_id),
    )
    return SearchTaskResponse(status=task.status, id=task.id)


@search_router.get("/{task_id}/status")
def get_task_status(task_id: str):
    status = get_task_status(task_id)
    return status