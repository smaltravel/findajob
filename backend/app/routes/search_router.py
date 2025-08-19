from fastapi import APIRouter

from app.schemas.task import SearchTaskRequest, SearchTaskResponse
from app.tasks.search import run_search_pipeline
from app.config.loader import settings

search_router = APIRouter(
    prefix="/search",
    tags=["Search"]
)


@search_router.post("/", response_model=SearchTaskResponse)
def search_jobs(request: SearchTaskRequest):
    webhook_url = f"{settings.WEBHOOK_BASE_URL}/api/jobs"

    task = run_search_pipeline.s(
        request.spider_config.model_dump(mode="json"),
        request.ai_provider_config.model_dump(mode="json"),
        request.ai_provider,
        request.user_cv.model_dump(mode="json"),
        webhook_url
    ).apply_async()
    return SearchTaskResponse(status=task.status, id=task.id)


@search_router.get("/{task_id}/status")
def get_task_status(task_id: str):
    # TODO: Implement proper task status checking
    return {"status": "unknown", "task_id": task_id}
