from typing import List
from sqlalchemy.orm import Session

from app.models import Job, JobMeta, Employer
from app.schemas.task import AIProcessedJobResult


def get_jobs(db: Session) -> List[Job]:
    return db.query(Job).all()


def get_job(db: Session, job_id: int) -> Job:
    return db.query(Job).filter(Job.id == job_id).first()


def add_job_entry(db: Session, job_entry: AIProcessedJobResult) -> None:
    # Create or get employer
    employer = db.query(Employer).filter(
        Employer.name == job_entry.employer).first()

    if not employer:
        employer = Employer(
            name=job_entry.employer,
            url=job_entry.employer_url,
            industries=job_entry.industries
        )
        db.add(employer)
        db.flush()  # Get the ID

    # Create job
    job = Job(
        job_id=job_entry.job_id,
        title=job_entry.job_title,
        location=job_entry.job_location,
        url=job_entry.job_url,
        status="new",
        source=job_entry.source,
        employer_id=employer.id
    )
    db.add(job)
    db.flush()  # Get the job ID

    # Create job meta
    job_meta = JobMeta(
        job_id=job.id,
        job_description=job_entry.job_description,
        employment_type=job_entry.employment_type,
        job_function=job_entry.job_function,
        seniority_level=job_entry.seniority_level,
        ai_metadata=job_entry.job_summary,
        cover_letter=job_entry.cover_letter
    )
    db.add(job_meta)

    db.commit()


def delete_job(db: Session, job_id: int) -> None:
    db_job = get_job(db, job_id)
    if db_job:
        db.delete(db_job)
        db.commit()
    return


def update_job_status(db: Session, job_id: int, status: str) -> bool:
    db_job = get_job(db, job_id)
    if not db_job:
        return False
    
    db_job.status = status
    db.commit()
    return True
