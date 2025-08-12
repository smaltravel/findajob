from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import asyncio
from typing import List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import os

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


class TaskQueueItem(BaseModel):
    id: int
    run_id: str
    service_name: str
    status: str
    created_at: str


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

            # Create task queue table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_queue (
                    id SERIAL PRIMARY KEY,
                    run_id VARCHAR(255) NOT NULL,
                    service_name VARCHAR(50) NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP NULL,
                    completed_at TIMESTAMP NULL
                )
            """)

            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Database initialization error: {e}")


def create_task_in_queue(run_id: str, service_name: str):
    """Create a task in the queue for a specific service"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO task_queue (run_id, service_name) VALUES (%s, %s)",
                (run_id, service_name)
            )
            conn.commit()
            cursor.close()
            conn.close()
            print(
                f"Created task in queue for {service_name} with run_id: {run_id}")
            return True
        except Exception as e:
            print(f"Error creating task in queue: {e}")
            return False
    return False


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

    # Create first task in queue for Service 1
    create_task_in_queue(run_id, "service_1")

    webhook_url = f"/pipeline/status/{run_id}"

    return PipelineResponse(
        run_id=run_id,
        webhook_url=webhook_url,
        status="started"
    )


@app.get("/pipeline/status/{run_id}")
async def get_pipeline_status(run_id: str):
    """Get the status of a pipeline run"""
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

    raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/queue/status", response_model=List[TaskQueueItem])
async def get_queue_status():
    """Get the current status of all tasks in the queue"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT id, run_id, service_name, status, created_at
                FROM task_queue
                ORDER BY created_at DESC
            """)

            results = cursor.fetchall()
            cursor.close()
            conn.close()

            data = []
            for row in results:
                data.append(TaskQueueItem(
                    id=row["id"],
                    run_id=row["run_id"],
                    service_name=row["service_name"],
                    status=row["status"],
                    created_at=str(row["created_at"])
                ))

            return data

        except Exception as e:
            print(f"Error fetching queue status: {e}")
            raise HTTPException(
                status_code=500, detail="Internal server error")

    raise HTTPException(status_code=500, detail="Database connection failed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
