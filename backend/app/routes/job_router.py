from typing import List
from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.config.database import get_db
from app.schemas.job import Job, JobAiSummary, JobAiCoverLetter, JobMeta, Employer
from app.schemas.task import AIProcessedJobResult
from app.services.job_service import get_jobs, get_job, delete_job, add_job_entry

job_router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)


@job_router.get("/", response_model=List[Job])
def job_list(db: Session = Depends(get_db)):
    jobs: List[Job] = []
    for job in get_jobs(db):
        jobs.append(Job(
            id=job.id,
            title=job.title,
            location=job.location,
            url=job.url,
            employer=Employer(
                id=job.employer.id,
                name=job.employer.name,
                url=job.employer.url,
                industries=job.employer.industries
            ),
            meta=JobMeta(
                job_description=job.meta.job_description,
                seniority_level=job.meta.seniority_level,
                employment_type=job.meta.employment_type,
                job_function=job.meta.job_function,
                ai_metadata=JobAiSummary.model_validate_json(
                    job.meta.ai_metadata),
                cover_letter=JobAiCoverLetter.model_validate_json(
                    job.meta.cover_letter)
            )
        ))
    return jobs


@job_router.get("/{job_id}", response_model=Job)
def job_detail(job_id: int, db: Session = Depends(get_db)):
    db_job = get_job(db, job_id)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return db_job


@job_router.delete("/{job_id}")
def job_delete(job_id: int, db: Session = Depends(get_db)):
    db_job = get_job(db, job_id)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    delete_job(db, job_id)
    return {"message": "Job deleted successfully"}


@job_router.post("/")
def job_create(job_entry: AIProcessedJobResult, db: Session = Depends(get_db)):
    add_job_entry(db, job_entry)
    return {"message": "Job created successfully"}
