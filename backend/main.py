from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import asyncio
from typing import List, Dict, Any, Optional
import os
from celery_tasks import run_complete_pipeline, continue_pipeline
from celery.result import AsyncResult
from celery_app import celery_app

# SQLAlchemy imports
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from models import Base, Task, Job, JobMeta, Employer

app = FastAPI(title="FindAJob AI Pipeline API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    # In production, restrict this to your frontend domain
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "postgres"),
    "database": os.getenv("DB_DB", "findajob"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "port": os.getenv("DB_PORT", "5432")
}

# SQLAlchemy database URL
DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

# Create SQLAlchemy engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class PipelineResponse(BaseModel):
    run_id: str
    webhook_url: str
    status: str


class TaskData(BaseModel):
    run_id: str
    jobs_processed: int
    total_jobs: int
    status: str


class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: Dict[str, Any] = None
    error: str = None


class PipelineTask(BaseModel):
    run_id: str
    pipeline_task_id: str
    service1_task_id: str = None
    service2_task_id: str = None
    status: str = "started"


class PipelineConfig(BaseModel):
    keywords: str = "python developer"
    location: str = "remote"
    max_jobs: int = 10
    seniority: int = 3
    ai_provider: str = "template"
    # CV data as JSON object instead of file path
    cv_content: Optional[dict] = None
    ollama_model: str = "deepseek-r1:7b"
    ollama_url: str = "http://localhost:11434"
    google_model: str = "gemini-2.5-flash-lite"
    google_api_key: Optional[str] = None


# In-memory storage for pipeline task tracking
pipeline_tasks: Dict[str, PipelineTask] = {}
pipeline_configs: Dict[str, PipelineConfig] = {}


def get_db_session():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        print(f"Database session error: {e}")
        db.close()
        return None


def safe_get_task_result(task_result):
    """Safely get task result with proper error handling"""
    try:
        if task_result.ready():
            if task_result.successful():
                return task_result.result
            else:
                # Task failed, get error info safely
                try:
                    info = task_result.info
                    if isinstance(info, dict) and 'exc_type' in info:
                        return None  # Task failed with proper exception info
                    else:
                        return None  # Task failed but no proper exception info
                except Exception:
                    return None  # Can't get exception info
        return None  # Task not ready
    except Exception as e:
        print(f"Error getting task result: {e}")
        return None


def init_database():
    """Initialize database tables if they don't exist"""
    try:
        # Create all tables using the unified Base
        Base.metadata.create_all(bind=engine)
        print("Database tables initialized successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")


def check_and_continue_pipeline(run_id: str):
    """Check pipeline status and continue if needed"""
    if run_id not in pipeline_tasks:
        return

    pipeline_task = pipeline_tasks[run_id]

    # Check if Service 1 completed
    if pipeline_task.service1_task_id and not pipeline_task.service2_task_id:
        try:
            service1_result = AsyncResult(
                pipeline_task.service1_task_id, app=celery_app)

            # Safely get task result
            result = safe_get_task_result(service1_result)
            if result is not None:
                # Service 1 completed, start Service 2
                jobs_found = result.get('jobs_found', 0)
                if jobs_found is not None:
                    print(
                        f"Service 1 completed for {run_id}, starting Service 2 with {jobs_found} jobs found")
                    # Start Service 2 (AI Job Processor)
                    service2_task = continue_pipeline.delay(run_id, jobs_found)
                    pipeline_task.service2_task_id = service2_task.id
                    pipeline_task.status = "service2_started"
                    print(
                        f"Service 2 (AI Job Processor) started: {service2_task.id}")
            elif service1_result.ready():
                # Service 1 failed
                print(f"Service 1 failed for {run_id}")
                pipeline_task.status = "service1_failed"
        except Exception as e:
            print(f"Error checking Service 1 status for {run_id}: {e}")
            # Don't update status, just log the error

    # Check if Service 2 completed
    elif pipeline_task.service2_task_id:
        try:
            service2_result = AsyncResult(
                pipeline_task.service2_task_id, app=celery_app)

            # Safely get task result
            result = safe_get_task_result(service2_result)
            if result is not None:
                # Service 2 completed, pipeline is done
                pipeline_task.status = "completed"
                print(f"Pipeline completed for {run_id}")
            elif service2_result.ready():
                # Service 2 failed
                print(f"Service 2 failed for {run_id}")
                pipeline_task.status = "service2_failed"
        except Exception as e:
            print(f"Error checking Service 2 status for {run_id}: {e}")
            # Don't update status, just log the error


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_database()


@app.get("/")
async def root():
    return {"message": "FindAJob Pipeline API"}


@app.post("/api/pipeline", response_model=PipelineResponse)
async def run_pipeline(config: PipelineConfig = Body(...)):
    """Start the pipeline and return a webhook URL for status checking"""
    run_id = str(uuid.uuid4())

    print(f"🚀 Starting AI pipeline with parameters:")
    print(f"   Keywords: {config.keywords}")
    print(f"   Location: {config.location}")
    print(f"   Max Jobs: {config.max_jobs}")
    print(f"   Seniority: {config.seniority}")
    print(f"   AI Provider: {config.ai_provider}")

    # Create initial task record using SQLAlchemy
    db = get_db_session()
    if db:
        try:
            task = Task(
                run_id=run_id,
                status="pending"
            )
            db.add(task)
            db.commit()
            db.close()
        except Exception as e:
            print(f"Error creating task: {e}")
            if db:
                db.close()

    # Start the Celery pipeline task with crawling parameters and AI configuration
    pipeline_task = run_complete_pipeline.delay(
        run_id, config.keywords, config.location, config.max_jobs, config.seniority,
        config.ai_provider, config.google_model if config.ai_provider == "google" else config.ollama_model,
        config.ollama_url if config.ai_provider == "ollama" else "http://localhost:11434",
        config.google_api_key, 120, 0.7, config.cv_content)
    print(
        f"Started Celery pipeline task: {pipeline_task.id} for run_id: {run_id}")

    # Store pipeline task info and configuration
    pipeline_tasks[run_id] = PipelineTask(
        run_id=run_id,
        pipeline_task_id=pipeline_task.id,
        status="started"
    )

    # Store the configuration for later use
    pipeline_configs[run_id] = config

    # Start background task to monitor and continue pipeline
    asyncio.create_task(monitor_pipeline(run_id))

    webhook_url = f"/api/pipeline/status/{run_id}"

    return PipelineResponse(
        run_id=run_id,
        webhook_url=webhook_url,
        status="started"
    )


async def monitor_pipeline(run_id: str):
    """Monitor pipeline progress and continue when services complete"""
    if run_id not in pipeline_tasks:
        return

    pipeline_task = pipeline_tasks[run_id]

    # Wait for pipeline task to start Service 1
    while True:
        try:
            pipeline_result = AsyncResult(
                pipeline_task.pipeline_task_id, app=celery_app)

            # Safely get task result
            result = safe_get_task_result(pipeline_result)
            if result is not None:
                if result.get('status') == 'service1_started':
                    pipeline_task.service1_task_id = result.get(
                        'service1_task_id')
                    pipeline_task.status = "service1_started"
                    print(
                        f"Service 1 started for {run_id}: {pipeline_task.service1_task_id}")
                    break
                else:
                    print(f"Unexpected pipeline result: {result}")
                    return
            elif pipeline_result.ready():
                print(f"Pipeline task failed for {run_id}")
                return
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error monitoring pipeline: {e}")
            return

    # Now monitor Service 1
    while True:
        try:
            if pipeline_task.service1_task_id:
                service1_result = AsyncResult(
                    pipeline_task.service1_task_id, app=celery_app)

                # Safely get task result
                result = safe_get_task_result(service1_result)
                if result is not None:
                    jobs_found = result.get('jobs_found', 0)
                    if jobs_found is not None:
                        print(
                            f"Service 1 completed for {run_id}, starting Service 2 (AI Job Processor)")
                        # Start Service 2 (AI Job Processor)
                        stored_config = pipeline_configs.get(run_id)
                        if stored_config:
                            service2_task = continue_pipeline.delay(
                                run_id, jobs_found, stored_config.ai_provider, stored_config.google_model if stored_config.ai_provider == "google" else stored_config.ollama_model,
                                stored_config.ollama_url if stored_config.ai_provider == "ollama" else "http://localhost:11434",
                                stored_config.google_api_key, 120, 0.7, stored_config.cv_content)
                        else:
                            # Fallback to default configuration
                            service2_task = continue_pipeline.delay(
                                run_id, jobs_found, "ollama", "deepseek-r1:7b", "http://localhost:11434", None, 120, 0.7, None)
                        pipeline_task.service2_task_id = service2_task.id
                        pipeline_task.status = "service2_started"
                        print(
                            f"Service 2 (AI Job Processor) started: {service2_task.id}")
                        break
                elif service1_result.ready():
                    print(f"Service 1 failed for {run_id}")
                    return
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error monitoring Service 1: {e}")
            return

    # Finally monitor Service 2
    while True:
        try:
            if pipeline_task.service2_task_id:
                service2_result = AsyncResult(
                    pipeline_task.service2_task_id, app=celery_app)

                # Safely get task result
                result = safe_get_task_result(service2_result)
                if result is not None:
                    print(f"Pipeline completed for {run_id}")
                    pipeline_task.status = "completed"
                    break
                elif service2_result.ready():
                    print(f"Service 2 failed for {run_id}")
                    return
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error monitoring Service 2: {e}")
            return


@app.get("/api/pipeline/status/{run_id}")
async def get_pipeline_status(run_id: str):
    """Get the status of a pipeline run"""
    # Check pipeline task status first
    if run_id in pipeline_tasks:
        pipeline_task = pipeline_tasks[run_id]
        check_and_continue_pipeline(run_id)  # Update status if needed

        if pipeline_task.status == "completed":
            # Get final results from database using SQLAlchemy
            db = get_db_session()
            if db:
                try:
                    # Count processed jobs (JobMeta with cover_letter)
                    processed_count = db.query(JobMeta).join(Job).join(Task).filter(
                        Task.run_id == run_id,
                        JobMeta.cover_letter.isnot(None)
                    ).count()

                    # Count total jobs
                    total_count = db.query(Job).join(Task).filter(
                        Task.run_id == run_id
                    ).count()

                    db.close()

                    return {
                        "run_id": run_id,
                        "status": "completed",
                        "jobs_processed": processed_count,
                        "total_jobs": total_count,
                        "message": f"Successfully processed {processed_count} out of {total_count} jobs"
                    }
                except Exception as e:
                    print(f"Error getting job results: {e}")

        # Return current pipeline status
        return {
            "run_id": run_id,
            "status": pipeline_task.status,
            "pipeline_task_id": pipeline_task.pipeline_task_id,
            "service1_task_id": pipeline_task.service1_task_id,
            "service2_task_id": pipeline_task.service2_task_id
        }

    # Fallback to database check using SQLAlchemy
    db = get_db_session()
    if db:
        try:
            # Check if task exists
            task = db.query(Task).filter(Task.run_id == run_id).first()

            if not task:
                raise HTTPException(
                    status_code=404, detail="Pipeline not found")

            # Count processed jobs
            processed_count = db.query(JobMeta).join(Job).join(Task).filter(
                Task.run_id == run_id,
                JobMeta.cover_letter.isnot(None)
            ).count()

            # Count total jobs
            total_count = db.query(Job).join(Task).filter(
                Task.run_id == run_id
            ).count()

            db.close()

            if processed_count > 0:
                return {
                    "run_id": run_id,
                    "status": "completed",
                    "jobs_processed": processed_count,
                    "total_jobs": total_count,
                    "message": f"Successfully processed {processed_count} out of {total_count} jobs"
                }
            else:
                return {
                    "run_id": run_id,
                    "status": "processing",
                    "jobs_processed": 0,
                    "total_jobs": total_count
                }

        except HTTPException:
            # Re-raise HTTP exceptions (like 404) without wrapping them
            raise
        except Exception as e:
            print(f"Error checking status: {e}")
            raise HTTPException(
                status_code=500, detail="Internal server error")

    raise HTTPException(status_code=500, detail="Database connection failed")


@app.get("/data", response_model=List[TaskData])
async def get_data():
    """Get all data from the database using SQLAlchemy"""
    db = get_db_session()
    if db:
        try:
            # Get task statistics using SQLAlchemy
            tasks = db.query(Task).all()

            data = []
            for task in tasks:
                # Count jobs for this task
                total_jobs = db.query(Job).filter(
                    Job.task_id == task.id).count()

                # Count processed jobs for this task
                processed_jobs = db.query(JobMeta).join(Job).filter(
                    Job.task_id == task.id,
                    JobMeta.cover_letter.isnot(None)
                ).count()

                data.append(TaskData(
                    run_id=task.run_id,
                    jobs_processed=processed_jobs,
                    total_jobs=total_jobs,
                    status=task.status
                ))

            db.close()
            return data

        except Exception as e:
            print(f"Error fetching data: {e}")
            raise HTTPException(
                status_code=500, detail="Internal server error")

    raise HTTPException(status_code=500, detail="Database connection failed")


@app.get("/api/jobs/{run_id}")
async def get_jobs(run_id: str):
    """Get all jobs for a specific pipeline run using SQLAlchemy"""
    db = get_db_session()
    if db:
        try:
            # First get the task
            task = db.query(Task).filter(Task.run_id == run_id).first()
            if not task:
                db.close()
                raise HTTPException(
                    status_code=404, detail="Pipeline not found")

            # Get jobs for this task
            jobs = db.query(Job).filter(Job.task_id == task.id).all()
            db.close()

            # Convert to list of dictionaries
            jobs_data = []
            for job in jobs:
                job_dict = {
                    "id": job.id,
                    "job_id": job.job_id,
                    "title": job.title,
                    "location": job.location,
                    "url": job.url,
                    "run_id": run_id
                }

                # Add meta data if available
                if job.meta:
                    job_dict.update({
                        "job_description": job.meta.job_description,
                        "employment_type": job.meta.employment_type,
                        "job_function": job.meta.job_function,
                        "seniority_level": job.meta.seniority_level,
                        "industries": job.meta.industries
                    })

                # Add employer data if available
                if job.employer:
                    job_dict.update({
                        "employer": job.employer.name,
                        "employer_url": job.employer.url
                    })

                jobs_data.append(job_dict)

            return {
                "run_id": run_id,
                "jobs_count": len(jobs_data),
                "jobs": jobs_data
            }

        except Exception as e:
            print(f"Error fetching jobs: {e}")
            raise HTTPException(
                status_code=500, detail="Internal server error")

    raise HTTPException(status_code=500, detail="Database connection failed")


@app.get("/api/jobs")
async def get_all_jobs():
    """Get all jobs from all pipeline runs using SQLAlchemy"""
    db = get_db_session()
    if db:
        try:
            jobs = db.query(Job).join(Task).all()
            db.close()

            # Convert to list of dictionaries
            jobs_data = []
            for job in jobs:
                job_dict = {
                    "id": job.id,
                    "job_id": job.job_id,
                    "title": job.title,
                    "location": job.location,
                    "url": job.url,
                    "pipeline_created_at": job.task.created_at if job.task else None
                }

                # Add meta data if available
                if job.meta:
                    job_dict.update({
                        "job_description": job.meta.job_description,
                        "employment_type": job.meta.employment_type,
                        "job_function": job.meta.job_function,
                        "seniority_level": job.meta.seniority_level,
                        "industries": job.meta.industries
                    })

                # Add employer data if available
                if job.employer:
                    job_dict.update({
                        "employer": job.employer.name,
                        "employer_url": job.employer.url
                    })

                jobs_data.append(job_dict)

            return {
                "total_jobs": len(jobs_data),
                "jobs": jobs_data
            }

        except Exception as e:
            print(f"Error fetching all jobs: {e}")
            raise HTTPException(
                status_code=500, detail="Internal server error")

    raise HTTPException(status_code=500, detail="Database connection failed")


@app.get("/api/processed-jobs/{run_id}")
async def get_processed_jobs(run_id: str):
    """Get all AI-processed jobs for a specific pipeline run using SQLAlchemy"""
    db = get_db_session()
    if db:
        try:
            # First get the task
            task = db.query(Task).filter(Task.run_id == run_id).first()
            if not task:
                db.close()
                raise HTTPException(
                    status_code=404, detail="Pipeline not found")

            # Get processed jobs for this task
            processed_jobs = db.query(JobMeta).join(Job).filter(
                Job.task_id == task.id,
                JobMeta.cover_letter.isnot(None)
            ).all()
            db.close()

            # Convert to list of dictionaries
            processed_jobs_data = []
            for job_meta in processed_jobs:
                job_dict = {
                    "id": job_meta.id,
                    "job_id": job_meta.job_id,
                    "run_id": run_id,
                    "job_title": job_meta.job.title if job_meta.job else None,
                    "employer": job_meta.job.employer.name if job_meta.job and job_meta.job.employer else None,
                    "job_location": job_meta.job.location if job_meta.job else None,
                    "cover_letter": job_meta.cover_letter,
                    "job_summary": job_meta.job_description,
                    "processing_status": "completed" if job_meta.cover_letter else "pending"
                }
                processed_jobs_data.append(job_dict)

            return {
                "run_id": run_id,
                "processed_jobs_count": len(processed_jobs_data),
                "processed_jobs": processed_jobs_data
            }

        except Exception as e:
            print(f"Error fetching processed jobs: {e}")
            raise HTTPException(
                status_code=500, detail="Internal server error")

    raise HTTPException(status_code=500, detail="Database connection failed")


@app.get("/api/processed-jobs")
async def get_all_processed_jobs():
    """Get all AI-processed jobs from all pipeline runs using SQLAlchemy"""
    db = get_db_session()
    if db:
        try:
            processed_jobs = db.query(JobMeta).join(Job).filter(
                JobMeta.cover_letter.isnot(None)
            ).all()
            db.close()

            # Convert to list of dictionaries
            processed_jobs_data = []
            for job_meta in processed_jobs:
                job_dict = {
                    "id": job_meta.id,
                    "job_id": job_meta.job_id,
                    "run_id": job_meta.job.task.run_id if job_meta.job and job_meta.job.task else None,
                    "job_title": job_meta.job.title if job_meta.job else None,
                    "employer": job_meta.job.employer.name if job_meta.job and job_meta.job.employer else None,
                    "job_location": job_meta.job.location if job_meta.job else None,
                    "pipeline_created_at": job_meta.job.task.created_at if job_meta.job and job_meta.job.task else None,
                    "cover_letter": job_meta.cover_letter,
                    "job_summary": job_meta.job_description,
                    "processing_status": "completed" if job_meta.cover_letter else "pending"
                }
                processed_jobs_data.append(job_dict)

            return {
                "total_processed_jobs": len(processed_jobs_data),
                "processed_jobs": processed_jobs_data
            }

        except Exception as e:
            print(f"Error fetching all processed jobs: {e}")
            raise HTTPException(
                status_code=500, detail="Internal server error")

    raise HTTPException(status_code=500, detail="Database connection failed")


@app.get("/tasks/{task_id}/status", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Get the status of a specific Celery task"""
    try:
        task_result = AsyncResult(task_id, app=celery_app)

        # Safely get task result
        result = safe_get_task_result(task_result)
        if result is not None:
            return TaskStatus(
                task_id=task_id,
                status="completed",
                result=result
            )
        elif task_result.ready():
            # Task failed
            return TaskStatus(
                task_id=task_id,
                status="failed",
                error="Task failed"
            )
        else:
            # Task is still running
            return TaskStatus(
                task_id=task_id,
                status=task_result.state,
                result=None
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting task status: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db = get_db_session()
    db_status = "connected" if db else "disconnected"
    if db:
        db.close()

    return {
        "status": "healthy",
        "database": db_status,
        "pipeline_tasks": len(pipeline_tasks)
    }


class JobStatusUpdate(BaseModel):
    status: str


class JobDelete(BaseModel):
    job_id: int


@app.put("/api/jobs/{job_id}/status")
async def update_job_status(job_id: int, status_update: JobStatusUpdate):
    """Update the status of a specific job using SQLAlchemy"""
    db = get_db_session()
    if db:
        try:
            # Find the job
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                db.close()
                raise HTTPException(status_code=404, detail="Job not found")

            # Update job status (assuming we add a status field to Job model)
            # For now, we'll update the task status
            if hasattr(job, 'task'):
                job.task.status = status_update.status

            db.commit()
            db.close()

            return {"message": "Job status updated successfully", "job_id": job_id, "new_status": status_update.status}

        except Exception as e:
            print(f"Error updating job status: {e}")
            if db:
                db.close()
            raise HTTPException(
                status_code=500, detail="Internal server error")

    raise HTTPException(status_code=500, detail="Database connection failed")


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: int):
    """Delete a specific job and its processed data using SQLAlchemy"""
    db = get_db_session()
    if db:
        try:
            # Find the job
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                db.close()
                raise HTTPException(status_code=404, detail="Job not found")

            # Delete the job (cascade will handle related records)
            db.delete(job)
            db.commit()
            db.close()

            return {"message": "Job deleted successfully", "job_id": job_id}

        except Exception as e:
            print(f"Error deleting job: {e}")
            if db:
                db.close()
            raise HTTPException(
                status_code=500, detail="Internal server error")

    raise HTTPException(status_code=500, detail="Database connection failed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
