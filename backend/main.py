from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import asyncio
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from celery_tasks import run_complete_pipeline, continue_pipeline
from celery.result import AsyncResult
from celery_app import celery_app

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
    cv_path: str = "/workspace/cv.json"
    ollama_model: str = "deepseek-r1:7b"
    ollama_url: str = "http://localhost:11434"
    google_model: str = "gemini-2.5-flash-lite"
    google_api_key: Optional[str] = None


# In-memory storage for pipeline task tracking
pipeline_tasks: Dict[str, PipelineTask] = {}


def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
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
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()

            # Drop existing tables to recreate with correct schema
            cursor.execute("DROP TABLE IF EXISTS processed_jobs CASCADE")
            cursor.execute("DROP TABLE IF EXISTS jobs CASCADE")
            cursor.execute("DROP TABLE IF EXISTS tasks CASCADE")

            # Create tasks table first (referenced by other tables)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    run_id VARCHAR(255) UNIQUE NOT NULL,
                    status VARCHAR(50) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create jobs table for storing crawled job data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id SERIAL PRIMARY KEY,
                    spider_source VARCHAR(255) NOT NULL,
                    job_id VARCHAR(255) UNIQUE,
                    job_title TEXT,
                    job_location TEXT,
                    job_url TEXT,
                    job_description TEXT,
                    employer VARCHAR(255),
                    employer_url TEXT,
                    employment_type VARCHAR(100),
                    job_function VARCHAR(255),
                    seniority_level VARCHAR(100),
                    industries TEXT,
                    run_id VARCHAR(255) REFERENCES tasks(run_id),
                    status VARCHAR(50) NOT NULL DEFAULT 'new',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create processed_jobs table for storing AI-processed job data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_jobs (
                    id SERIAL PRIMARY KEY,
                    job_id INTEGER REFERENCES jobs(id),
                    run_id VARCHAR(255) REFERENCES tasks(run_id),
                    cover_letter TEXT,
                    job_summary TEXT,
                    processing_status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_run_id ON jobs(run_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_job_id ON jobs(job_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON jobs(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON jobs(created_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_job_title ON jobs(job_title)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_employer ON jobs(employer)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_processed_jobs_job_id ON processed_jobs(job_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_processed_jobs_run_id ON processed_jobs(run_id)
            """)

            conn.commit()
            cursor.close()
            conn.close()
            print("Database tables initialized successfully")
        except Exception as e:
            print(f"Database initialization error: {e}")
            if conn:
                conn.close()


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
    print(f"   CV Path: {config.cv_path}")

    # Create initial task record
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tasks (run_id) VALUES (%s)",
                (run_id,)
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error creating task: {e}")

    # Start the Celery pipeline task with crawling parameters
    pipeline_task = run_complete_pipeline.delay(
        run_id, config.keywords, config.location, config.max_jobs, config.seniority)
    print(
        f"Started Celery pipeline task: {pipeline_task.id} for run_id: {run_id}")

    # Store pipeline task info
    pipeline_tasks[run_id] = PipelineTask(
        run_id=run_id,
        pipeline_task_id=pipeline_task.id,
        status="started"
    )

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
                        service2_task = continue_pipeline.delay(
                            run_id, jobs_found)
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
            # Get final results from database
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor(cursor_factory=RealDictCursor)
                    cursor.execute(
                        "SELECT COUNT(*) as processed_count FROM processed_jobs WHERE run_id = %s", (run_id,))
                    processed_count = cursor.fetchone()["processed_count"]

                    cursor.execute(
                        "SELECT COUNT(*) as total_count FROM jobs WHERE run_id = %s", (run_id,))
                    total_count = cursor.fetchone()["total_count"]

                    cursor.close()
                    conn.close()

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

    # Fallback to database check
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Check if task exists
            cursor.execute("SELECT * FROM tasks WHERE run_id = %s", (run_id,))
            task = cursor.fetchone()

            if not task:
                raise HTTPException(
                    status_code=404, detail="Pipeline not found")

            # Check if jobs were processed
            cursor.execute(
                "SELECT COUNT(*) as processed_count FROM processed_jobs WHERE run_id = %s", (run_id,))
            processed_count = cursor.fetchone()["processed_count"]

            cursor.execute(
                "SELECT COUNT(*) as total_count FROM jobs WHERE run_id = %s", (run_id,))
            total_count = cursor.fetchone()["total_count"]

            cursor.close()
            conn.close()

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
    """Get all data from the database"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Join tasks and jobs tables to get job processing statistics
            cursor.execute("""
                SELECT 
                    t.run_id, 
                    t.status,
                    COUNT(j.id) as total_jobs,
                    COUNT(pj.id) as jobs_processed
                FROM tasks t
                LEFT JOIN jobs j ON t.run_id = j.run_id
                LEFT JOIN processed_jobs pj ON t.run_id = pj.run_id
                GROUP BY t.run_id, t.status
                ORDER BY t.created_at DESC
            """)

            results = cursor.fetchall()
            cursor.close()
            conn.close()

            data = []
            for row in results:
                data.append(TaskData(
                    run_id=row["run_id"],
                    jobs_processed=row["jobs_processed"] or 0,
                    total_jobs=row["total_jobs"] or 0,
                    status=row["status"]
                ))

            return data

        except Exception as e:
            print(f"Error fetching data: {e}")
            raise HTTPException(
                status_code=500, detail="Internal server error")

    raise HTTPException(status_code=500, detail="Database connection failed")


@app.get("/api/jobs/{run_id}")
async def get_jobs(run_id: str):
    """Get all jobs for a specific pipeline run"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT * FROM jobs 
                WHERE run_id = %s 
                ORDER BY created_at DESC
            """, (run_id,))

            results = cursor.fetchall()
            cursor.close()
            conn.close()

            # Convert to list of dictionaries
            jobs = []
            for row in results:
                job = dict(row)
                jobs.append(job)

            return {
                "run_id": run_id,
                "jobs_count": len(jobs),
                "jobs": jobs
            }

        except Exception as e:
            print(f"Error fetching jobs: {e}")
            raise HTTPException(
                status_code=500, detail="Internal server error")

    raise HTTPException(status_code=500, detail="Database connection failed")


@app.get("/api/jobs")
async def get_all_jobs():
    """Get all jobs from all pipeline runs"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT j.*, t.created_at as pipeline_created_at
                FROM jobs j
                JOIN tasks t ON j.run_id = t.run_id
                ORDER BY j.created_at DESC
            """)

            results = cursor.fetchall()
            cursor.close()
            conn.close()

            # Convert to list of dictionaries
            jobs = []
            for row in results:
                job = dict(row)
                jobs.append(job)

            return {
                "total_jobs": len(jobs),
                "jobs": jobs
            }

        except Exception as e:
            print(f"Error fetching all jobs: {e}")
            raise HTTPException(
                status_code=500, detail="Internal server error")

    raise HTTPException(status_code=500, detail="Database connection failed")


@app.get("/api/processed-jobs/{run_id}")
async def get_processed_jobs(run_id: str):
    """Get all AI-processed jobs for a specific pipeline run"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT pj.*, j.job_title, j.employer, j.job_location
                FROM processed_jobs pj
                JOIN jobs j ON pj.job_id = j.id
                WHERE pj.run_id = %s 
                ORDER BY pj.created_at DESC
            """, (run_id,))

            results = cursor.fetchall()
            cursor.close()
            conn.close()

            # Convert to list of dictionaries
            processed_jobs = []
            for row in results:
                job = dict(row)
                processed_jobs.append(job)

            return {
                "run_id": run_id,
                "processed_jobs_count": len(processed_jobs),
                "processed_jobs": processed_jobs
            }

        except Exception as e:
            print(f"Error fetching processed jobs: {e}")
            raise HTTPException(
                status_code=500, detail="Internal server error")

    raise HTTPException(status_code=500, detail="Database connection failed")


@app.get("/api/processed-jobs")
async def get_all_processed_jobs():
    """Get all AI-processed jobs from all pipeline runs"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT pj.*, j.job_title, j.employer, j.job_location, t.created_at as pipeline_created_at
                FROM processed_jobs pj
                JOIN jobs j ON pj.job_id = j.id
                JOIN tasks t ON pj.run_id = t.run_id
                ORDER BY pj.created_at DESC
            """)

            results = cursor.fetchall()
            cursor.close()
            conn.close()

            # Convert to list of dictionaries
            processed_jobs = []
            for row in results:
                job = dict(row)
                processed_jobs.append(job)

            return {
                "total_processed_jobs": len(processed_jobs),
                "processed_jobs": processed_jobs
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
    return {
        "status": "healthy",
        "database": "connected" if get_db_connection() else "disconnected",
        "pipeline_tasks": len(pipeline_tasks)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
