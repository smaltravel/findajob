from celery.result import AsyncResult
from app.celery import celery_app


def get_task_status(task_id: str) -> str:
    task: AsyncResult = celery_app.AsyncResult(task_id)
    if task.ready():
        if task.successful():
            return {
                "status": task.status,
            }
        else:
            return {
                "status": task.status,
                "error": task.traceback,
            }
    else:
        return {
            "status": task.status,
        }