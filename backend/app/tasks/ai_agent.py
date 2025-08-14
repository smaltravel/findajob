import subprocess
from app.celery import celery_app
from app.schemas.search import AIProviderConfig

@celery_app.task
def process_jobs_with_ai(config: AIProviderConfig, run_id: str):
    """
    Process jobs with AI agent.
    """
    
    cmd = [
        "python",
        "/workspace/tools/job_processor.py",
        "--runid", run_id,
        "--base_url", config.base_url,
        "--provider", config.provider,
        "--api_key", config.api_key,
    ]

    result = subprocess.run(
        cmd,
        cwd="/workspace/scrapy",
        capture_output=True,
        text=True,
        timeout=300,
    )

    return result.returncode
