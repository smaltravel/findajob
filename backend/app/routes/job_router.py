from typing import List
from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.config.database import get_db
from app.schemas.job import Job
from app.services.job_service import get_jobs, get_job, delete_job

job_router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)


@job_router.get("/", response_model=List[Job])
def job_list(db: Session = Depends(get_db)):
    return get_jobs(db)


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
