import subprocess
from app.celery import celery_app
from app.schemas.search import SpiderConfig

@celery_app.task
def crawl_jobs(config: SpiderConfig, run_id: str):
    """
    Crawl jobs from the web using Scrapy.
    """
    cmd = [
        "scrapy", "crawl", "linkedin",
        "-a", f"keywords={config.keywords}",
        "-a", f"location={config.location}",
        "-a", f"run_id={run_id}",
        "-a", f"max_jobs={config.max_jobs}",
        "-a", f"seniority={config.seniority}",
    ]

    result = subprocess.run(
        cmd,
        cwd="/workspace/scrapy",
        capture_output=True,
        text=True,
        timeout=300,
    )

    return result.returncode

