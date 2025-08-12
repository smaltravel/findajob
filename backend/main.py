from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import asyncio
from typing import List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from celery_tasks import run_complete_pipeline, continue_pipeline
from celery.result import AsyncResult
from celery_app import celery_app

app = FastAPI(title="FindAJob Pipeline API", version="1.0.0")

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
    random_value: int
    password: str


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


def init_database():
    """Initialize database tables if they don't exist"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()

            # Create tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    run_id VARCHAR(255) PRIMARY KEY,
                    random_value INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create passwords table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS passwords (
                    id SERIAL PRIMARY KEY,
                    run_id VARCHAR(255) REFERENCES tasks(run_id),
                    random_value INTEGER,
                    password VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Database initialization error: {e}")


def check_and_continue_pipeline(run_id: str):
    """Check pipeline status and continue if needed"""
    if run_id not in pipeline_tasks:
        return

    pipeline_task = pipeline_tasks[run_id]

    # Check if Service 1 completed
    if pipeline_task.service1_task_id and not pipeline_task.service2_task_id:
        service1_result = AsyncResult(
            pipeline_task.service1_task_id, app=celery_app)
        if service1_result.ready() and service1_result.successful():
            # Service 1 completed, start Service 2
            result = service1_result.result
            random_value = result.get('random_value')
            if random_value:
                print(
                    f"Service 1 completed for {run_id}, starting Service 2 with random value: {random_value}")
                # Start Service 2
                service2_task = continue_pipeline.delay(run_id, random_value)
                pipeline_task.service2_task_id = service2_task.id
                pipeline_task.status = "service2_started"
                print(f"Service 2 started: {service2_task.id}")

    # Check if Service 2 completed
    elif pipeline_task.service2_task_id:
        service2_result = AsyncResult(
            pipeline_task.service2_task_id, app=celery_app)
        if service2_result.ready() and service2_result.successful():
            # Service 2 completed, pipeline is done
            pipeline_task.status = "completed"
            print(f"Pipeline completed for {run_id}")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_database()


@app.get("/")
async def root():
    return {"message": "FindAJob Pipeline API"}


@app.post("/pipeline", response_model=PipelineResponse)
async def run_pipeline():
    """Start the pipeline and return a webhook URL for status checking"""
    run_id = str(uuid.uuid4())

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

    # Start the Celery pipeline task
    pipeline_task = run_complete_pipeline.delay(run_id)
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

    webhook_url = f"/pipeline/status/{run_id}"

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
            if pipeline_result.ready():
                if pipeline_result.successful():
                    result = pipeline_result.result
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
                else:
                    print(f"Pipeline task failed: {pipeline_result.info}")
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
                if service1_result.ready():
                    if service1_result.successful():
                        result = service1_result.result
                        random_value = result.get('random_value')
                        if random_value:
                            print(
                                f"Service 1 completed for {run_id}, starting Service 2")
                            # Start Service 2
                            service2_task = continue_pipeline.delay(
                                run_id, random_value)
                            pipeline_task.service2_task_id = service2_task.id
                            pipeline_task.status = "service2_started"
                            print(f"Service 2 started: {service2_task.id}")
                            break
                    else:
                        print(f"Service 1 failed: {service1_result.info}")
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
                if service2_result.ready():
                    if service2_result.successful():
                        print(f"Pipeline completed for {run_id}")
                        pipeline_task.status = "completed"
                        break
                    else:
                        print(f"Service 2 failed: {service2_result.info}")
                        return
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error monitoring Service 2: {e}")
            return


@app.get("/pipeline/status/{run_id}")
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
                        "SELECT * FROM passwords WHERE run_id = %s", (run_id,))
                    password_record = cursor.fetchone()
                    cursor.close()
                    conn.close()

                    if password_record:
                        return {
                            "run_id": run_id,
                            "status": "completed",
                            "random_value": password_record["random_value"],
                            "password": password_record["password"]
                        }
                except Exception as e:
                    print(f"Error getting password: {e}")

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

            # Check if password was generated
            cursor.execute(
                "SELECT * FROM passwords WHERE run_id = %s", (run_id,))
            password_record = cursor.fetchone()

            cursor.close()
            conn.close()

            if password_record:
                return {
                    "run_id": run_id,
                    "status": "completed",
                    "random_value": password_record["random_value"],
                    "password": password_record["password"]
                }
            else:
                return {
                    "run_id": run_id,
                    "status": "processing",
                    "random_value": task["random_value"] if task["random_value"] else None
                }

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

            # Join tasks and passwords tables
            cursor.execute("""
                SELECT t.run_id, t.random_value, p.password
                FROM tasks t
                LEFT JOIN passwords p ON t.run_id = p.run_id
                ORDER BY t.created_at DESC
            """)

            results = cursor.fetchall()
            cursor.close()
            conn.close()

            data = []
            for row in results:
                data.append(TaskData(
                    run_id=row["run_id"],
                    random_value=row["random_value"] or 0,
                    password=row["password"] or "Not generated yet"
                ))

            return data

        except Exception as e:
            print(f"Error fetching data: {e}")
            raise HTTPException(
                status_code=500, detail="Internal server error")

    raise HTTPException(status_code=500, detail="Database connection failed")


@app.get("/tasks/{task_id}/status", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Get the status of a specific Celery task"""
    try:
        task_result = AsyncResult(task_id, app=celery_app)

        if task_result.ready():
            if task_result.successful():
                return TaskStatus(
                    task_id=task_id,
                    status="completed",
                    result=task_result.result
                )
            else:
                return TaskStatus(
                    task_id=task_id,
                    status="failed",
                    error=str(task_result.info)
                )
        else:
            # Task is still running
            return TaskStatus(
                task_id=task_id,
                status=task_result.state,
                result=task_result.info if task_result.info else None
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
