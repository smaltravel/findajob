from celery_app import celery_app
import psycopg2
import time
import os
import sys
from typing import List, Dict, Any

# Add tools directory to path for imports
sys.path.append('/workspace/tools')
sys.path.append('/app/tools')

# Import the job processor
try:
    from job_processor import JobProcessor
    from providers import OllamaProvider, GoogleAIProvider, AIProviderConfig
    JOB_PROCESSOR_AVAILABLE = True
    print("✅ Job processor imported successfully")
except ImportError as e:
    print(f"⚠️  Warning: Could not import job processor: {e}")
    print("   The system will use the fallback template-based processing method")
    JOB_PROCESSOR_AVAILABLE = False

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "postgres"),
    "database": os.getenv("DB_DB", "findajob"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "port": os.getenv("DB_PORT", "5432")
}

# AI Provider configuration
AI_CONFIG = {
    "provider": os.getenv("AI_PROVIDER", "ollama"),
    "model": os.getenv("AI_MODEL", "deepseek-r1:7b"),
    "base_url": os.getenv("AI_BASE_URL", "http://localhost:11434"),
    "api_key": os.getenv("AI_API_KEY", None),
    "timeout": int(os.getenv("AI_TIMEOUT", "120")),
    "temperature": float(os.getenv("AI_TEMPERATURE", "0.7"))
}


class PostgreSQLJobProcessor:
    """PostgreSQL-compatible version of JobProcessor for use in celery tasks."""

    def __init__(self, db_config: dict, ai_provider):
        """Initialize with database config and AI provider."""
        self.db_config = db_config
        self.ai_provider = ai_provider
        self.conn = None
        self.cursor = None

    def connect_database(self):
        """Connect to PostgreSQL database."""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            print("Connected to PostgreSQL database")
        except Exception as e:
            print(f"Failed to connect to database: {e}")
            raise e

    def get_new_jobs_by_runid(self, run_id: str) -> List[Dict]:
        """Get all new job records for the given run_id that haven't been processed yet."""
        query = '''
            SELECT j.* FROM jobs j
            LEFT JOIN processed_jobs pj ON j.id = pj.job_id
            WHERE j.run_id = %s AND pj.job_id IS NULL
            ORDER BY j.created_at ASC
        '''

        self.cursor.execute(query, (run_id,))
        results = self.cursor.fetchall()

        # Get column names
        columns = [desc[0] for desc in self.cursor.description]

        # Convert to list of dictionaries
        job_records = []
        for row in results:
            job = dict(zip(columns, row))
            job_records.append(job)

        print(f"Found {len(job_records)} new jobs for run_id: {run_id}")
        return job_records

    def process_job(self, job_data: Dict) -> Dict:
        """Process a single job record to generate cover letter and summary."""
        job_id = job_data['id']
        run_id = job_data['run_id']

        print(
            f"Processing job {job_id}: {job_data.get('job_title')} at {job_data.get('employer')}")

        try:
            # Update context for the current job
            self.ai_provider.set_job(job_data)

            # Generate cover letter
            print("Generating cover letter")
            cover_letter = self.ai_provider.cover_letter()

            # Generate job summary
            print("Generating job summary")
            job_summary = self.ai_provider.job_description()

            return {
                'job_id': job_id,
                'run_id': run_id,
                'cover_letter': cover_letter,
                'job_summary': job_summary,
                'processing_status': 'completed',
                'error_message': None
            }

        except Exception as e:
            print(f"Failed to process job {job_id}: {e}")
            return {
                'job_id': job_id,
                'run_id': run_id,
                'cover_letter': None,
                'job_summary': None,
                'processing_status': 'failed',
                'error_message': str(e)
            }

    def save_processed_job(self, processed_data: Dict):
        """Save processed job data to the database."""
        query = '''
            INSERT INTO processed_jobs (
                job_id, run_id, cover_letter, job_summary, processing_status, error_message, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        '''

        values = (
            processed_data['job_id'],
            processed_data['run_id'],
            processed_data['cover_letter'],
            processed_data['job_summary'],
            processed_data['processing_status'],
            processed_data['error_message']
        )

        self.cursor.execute(query, values)
        self.conn.commit()

        print(f"Saved processed job {processed_data['job_id']} to database")

    def process_jobs_by_runid(self, run_id: str):
        """Process all new jobs for the given run_id."""
        print(f"Starting to process jobs for run_id: {run_id}")

        # Get new jobs
        jobs = self.get_new_jobs_by_runid(run_id)

        if not jobs:
            print(f"No new jobs found for run_id: {run_id}")
            return

        # Process each job
        for i, job in enumerate(jobs, 1):
            print(f"Processing job {i}/{len(jobs)}")

            processed_data = self.process_job(job)
            self.save_processed_job(processed_data)

            # Add a small delay between requests to be respectful to the AI API
            time.sleep(1)

        print(f"Completed processing {len(jobs)} jobs for run_id: {run_id}")

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed")


def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None


@celery_app.task(bind=True, name="service_1.crawl_jobs")
def crawl_jobs(self, run_id: str, keywords: str = "python developer", location: str = "remote", max_jobs: int = 10, seniority: int = 3):
    """Service 1: Crawl job listings using Scrapy"""
    try:
        print(f"🕷️ Starting Service 1 (Job Crawler) for run_id: {run_id}")
        print(
            f"🔍 Keywords: {keywords}, Location: {location}, Max Jobs: {max_jobs}, Seniority: {seniority}")

        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={
                "status": "Starting job crawling",
                "run_id": run_id,
                "keywords": keywords,
                "location": location,
                "max_jobs": max_jobs
            }
        )

        # Import scrapy components
        import subprocess
        import os
        import json
        import time

        # Change to scrapy directory
        scrapy_dir = "/workspace/scrapy"
        if not os.path.exists(scrapy_dir):
            scrapy_dir = "/app/scrapy"  # Fallback path

        if not os.path.exists(scrapy_dir):
            raise Exception(f"Scrapy directory not found at {scrapy_dir}")

        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"status": "Running Scrapy spider", "run_id": run_id}
        )

        # Run the scrapy spider
        cmd = [
            "scrapy", "crawl", "linkedin",
            "-a", f"keywords={keywords}",
            "-a", f"location={location}",
            "-a", f"run_id={run_id}",
            "-a", f"max_jobs={max_jobs}",
            "-a", f"seniority={seniority}",
        ]

        print(f"Running command: {' '.join(cmd)}")

        # Execute scrapy command
        result = subprocess.run(
            cmd,
            cwd=scrapy_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )

        if result.returncode != 0:
            self.update_state(
                state="FAILURE",
                meta={
                    "status": f"Scrapy failed with return code {result.returncode}. Stdout: {result.stdout}, Stderr: {result.stderr}",
                    "run_id": run_id
                }
            )
            raise Exception(
                f"Scrapy failed with return code {result.returncode}")

        print("Scrapy spider completed successfully")

        # Update task status
        self.update_state(
            state="SUCCESS",
            meta={
                "status": "Job crawling completed successfully",
                "run_id": run_id
            }
        )

        return {
            "status": "success",
            "run_id": run_id,
            "keywords": keywords,
            "location": location,
            "max_jobs": max_jobs
        }

    except Exception as e:
        print(f"Service 1 (Job Crawler) failed: {e}")
        self.update_state(
            state="FAILURE",
            meta={"status": f"Service 1 failed: {str(e)}", "run_id": run_id}
        )
        raise e


@celery_app.task(bind=True, name="service_2.process_jobs_with_ai")
def process_jobs_with_ai(self, run_id: str):
    """Service 2: Process crawled jobs using AI to generate cover letters and summaries"""
    try:
        print(f"🤖 Starting Service 2 (AI Job Processor) for run_id: {run_id}")

        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"status": "Starting AI job processing", "run_id": run_id}
        )

        # Check if job processor is available
        if not JOB_PROCESSOR_AVAILABLE:
            self.update_state(
                state="FAILURE",
                meta={"status": "Job processor not available", "run_id": run_id}
            )
            raise Exception("Job processor not available")

        # Initialize AI provider
        try:
            if AI_CONFIG["provider"] == "ollama":
                ai_provider = OllamaProvider(
                    AIProviderConfig(
                        model=AI_CONFIG["model"],
                        base_url=AI_CONFIG["base_url"],
                        timeout=AI_CONFIG["timeout"],
                        temperature=AI_CONFIG["temperature"]
                    )
                )
            elif AI_CONFIG["provider"] == "google":
                if not AI_CONFIG["api_key"]:
                    raise Exception(
                        "API key is required for Google AI provider")
                ai_provider = GoogleAIProvider(
                    AIProviderConfig(
                        model=AI_CONFIG["model"],
                        api_key=AI_CONFIG["api_key"],
                        timeout=AI_CONFIG["timeout"],
                        temperature=AI_CONFIG["temperature"]
                    )
                )
            else:
                self.update_state(
                    state="FAILURE",
                    meta={"status": "Unknown AI provider", "run_id": run_id}
                )
                raise Exception("Unknown AI provider")
        except Exception as e:
            self.update_state(
                state="FAILURE",
                meta={"status": f"Failed to initialize AI provider: {e}",
                      "run_id": run_id}
            )
            raise e

        # Initialize job processor
        processor = PostgreSQLJobProcessor(DB_CONFIG, ai_provider)

        try:
            # Connect to database
            processor.connect_database()

            # Get new jobs for this run_id
            jobs = processor.get_new_jobs_by_runid(run_id)
            if not jobs:
                print(f"No new jobs found for run_id: {run_id}")
                self.update_state(
                    state="SUCCESS",
                    meta={
                        "status": "No jobs to process",
                        "run_id": run_id,
                        "jobs_processed": 0
                    }
                )
                return {
                    "status": "success",
                    "run_id": run_id,
                    "jobs_processed": 0,
                    "message": "No new jobs found to process"
                }

            print(f"Found {len(jobs)} new jobs to process with AI")

            # Update task status
            self.update_state(
                state="PROGRESS",
                meta={"status": "Processing jobs with AI",
                      "run_id": run_id, "total_jobs": len(jobs)}
            )

            # Process jobs using the processor
            processed_count = 0
            failed_count = 0

            for i, job in enumerate(jobs, 1):
                try:
                    print(
                        f"Processing job {i}/{len(jobs)}: {job.get('job_title', 'Unknown')}")

                    # Update progress
                    self.update_state(
                        state="PROGRESS",
                        meta={
                            "status": f"Processing job {i}/{len(jobs)}",
                            "run_id": run_id,
                            "current_job": i,
                            "total_jobs": len(jobs)
                        }
                    )

                    # Process job with AI using the processor
                    processed_data = processor.process_job(job)

                    if processed_data['processing_status'] == 'completed':
                        # Save the processed job
                        processor.save_processed_job(processed_data)
                        processed_count += 1
                        print(f"✅ Successfully processed job {i}")
                    else:
                        failed_count += 1
                        print(
                            f"❌ Failed to process job {i}: {processed_data['error_message']}")

                except Exception as e:
                    failed_count += 1
                    print(f"❌ Error processing job {i}: {e}")
                    # Continue with next job instead of failing completely

            print(f"🎉 AI processing completed for run_id: {run_id}")
            print(f"   Processed: {processed_count}")
            print(f"   Failed: {failed_count}")

            # Update task status
            self.update_state(
                state="SUCCESS",
                meta={
                    "status": "AI job processing completed successfully",
                    "run_id": run_id,
                    "jobs_processed": processed_count,
                    "jobs_failed": failed_count,
                    "total_jobs": len(jobs)
                }
            )

            return {
                "status": "success",
                "run_id": run_id,
                "jobs_processed": processed_count,
                "jobs_failed": failed_count,
                "total_jobs": len(jobs)
            }

        finally:
            # Always close the processor
            processor.close()

    except Exception as e:
        print(f"Service 2 (AI Job Processor) failed: {e}")
        self.update_state(
            state="FAILURE",
            meta={"status": f"Service 2 failed: {str(e)}", "run_id": run_id}
        )
        raise e


@celery_app.task(bind=True, name="pipeline.run_complete_pipeline")
def run_complete_pipeline(self, run_id: str, keywords: str = "python developer", location: str = "remote", max_jobs: int = 10, seniority: int = 3):
    """Run the complete pipeline: Service 1 (Job Crawling) -> Service 2 (Password Generation) using task chaining"""
    try:
        print(f"🚀 Starting complete pipeline for run_id: {run_id}")
        print(
            f"🔍 Job search parameters: {keywords} in {location}, max {max_jobs} jobs, seniority {seniority}")

        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"status": "Starting pipeline", "run_id": run_id}
        )

        # Step 1: Crawl jobs
        print("Step 1: Starting job crawling...")
        self.update_state(
            state="PROGRESS",
            meta={"status": "Step 1: Starting job crawling", "run_id": run_id}
        )

        # Call Service 1 (Job Crawler) and wait for it to complete
        # We can't use .wait() or .get() from within a task, so we'll just return
        # The backend will need to handle the chaining
        service1_task = crawl_jobs.delay(
            run_id, keywords, location, max_jobs, seniority)

        # Update task status to show Service 1 is running
        self.update_state(
            state="PROGRESS",
            meta={
                "status": "Step 1: Service 1 (Job Crawler) started",
                "run_id": run_id,
                "service1_task_id": service1_task.id
            }
        )

        print(f"Service 1 (Job Crawler) task started: {service1_task.id}")

        # Return the task ID so the backend can monitor it
        return {
            "status": "service1_started",
            "run_id": run_id,
            "service1_task_id": service1_task.id,
            "message": "Service 1 (Job Crawler) started. Monitor task status for completion."
        }

    except Exception as e:
        print(f"Pipeline failed: {e}")
        self.update_state(
            state="FAILURE",
            meta={"status": f"Pipeline failed: {str(e)}", "run_id": run_id}
        )
        raise e


@celery_app.task(bind=True, name="pipeline.continue_pipeline")
def continue_pipeline(self, run_id: str, jobs_found: int):
    """Continue pipeline after Service 1 completes - called by Service 1 callback"""
    try:
        print(
            f"🔄 Continuing pipeline for run_id: {run_id} with {jobs_found} jobs found")

        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"status": "Continuing pipeline",
                  "run_id": run_id, "jobs_found": jobs_found}
        )

        # Step 2: Process jobs with AI
        print("Step 2: Processing jobs with AI...")
        self.update_state(
            state="PROGRESS",
            meta={"status": "Step 2: Processing jobs with AI", "run_id": run_id}
        )

        # Call Service 2 (AI Job Processor)
        service2_task = process_jobs_with_ai.delay(run_id)

        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={
                "status": "Step 2: Service 2 (AI) started",
                "run_id": run_id,
                "service2_task_id": service2_task.id
            }
        )

        print(f"Service 2 (AI Job Processor) task started: {service2_task.id}")

        return {
            "status": "service2_started",
            "run_id": run_id,
            "service2_task_id": service2_task.id,
            "message": "Service 2 (AI Job Processor) started. Monitor task status for completion."
        }

    except Exception as e:
        print(f"Continue pipeline failed: {e}")
        self.update_state(
            state="FAILURE",
            meta={
                "status": f"Continue pipeline failed: {str(e)}", "run_id": run_id}
        )
        raise e
