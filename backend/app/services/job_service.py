from typing import List
from sqlalchemy.orm import Session

from app.models.job import Job


def get_jobs(db: Session) -> List[Job]:
    return db.query(Job).all()


def get_job(db: Session, job_id: int) -> Job:
    return db.query(Job).filter(Job.id == job_id).first()

def delete_job(db: Session, job_id: int) -> None:
    db_job = get_job(db, job_id)
    if db_job:
        db.delete(db_job)
        db.commit()
    return
