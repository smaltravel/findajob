from celery_app import celery_app
import psycopg2
import random
import string
import time
import os
import sys

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "postgres"),
    "database": os.getenv("DB_DB", "findajob"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "port": os.getenv("DB_PORT", "5432")
}


def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None


@celery_app.task(bind=True, name="service_1.generate_random_value")
def generate_random_value(self, run_id: str):
    """Service 1: Generate random value and store it in database"""
    try:
        print(f"🚀 Starting Service 1 for run_id: {run_id}")

        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"status": "Generating random value", "run_id": run_id}
        )

        # Simulate some processing time
        time.sleep(2)

        # Generate random value between 1 and 30
        random_value = random.randint(1, 30)
        print(f"Generated random value: {random_value}")

        # Store in database
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE tasks SET random_value = %s WHERE run_id = %s",
                    (random_value, run_id)
                )
                conn.commit()
                cursor.close()
                conn.close()
                print(
                    f"Successfully stored random value {random_value} for run_id {run_id}")

                # Update task status
                self.update_state(
                    state="SUCCESS",
                    meta={
                        "status": "Random value generated",
                        "run_id": run_id,
                        "random_value": random_value
                    }
                )

                return {
                    "status": "success",
                    "run_id": run_id,
                    "random_value": random_value
                }

            except Exception as e:
                print(f"Error storing random value: {e}")
                self.update_state(
                    state="FAILURE",
                    meta={"status": f"Error: {str(e)}", "run_id": run_id}
                )
                raise
        else:
            error_msg = "Failed to connect to database"
            print(error_msg)
            self.update_state(
                state="FAILURE",
                meta={"status": error_msg, "run_id": run_id}
            )
            raise Exception(error_msg)

    except Exception as e:
        print(f"Service 1 failed: {e}")
        self.update_state(
            state="FAILURE",
            meta={"status": f"Service 1 failed: {str(e)}", "run_id": run_id}
        )
        raise


@celery_app.task(bind=True, name="service_2.generate_password")
def generate_password(self, run_id: str):
    """Service 2: Generate password based on random value length"""
    try:
        print(f"🔐 Starting Service 2 for run_id: {run_id}")

        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"status": "Reading random value", "run_id": run_id}
        )

        # Get the random value
        random_value = get_random_value(run_id)
        if random_value is None:
            error_msg = f"No random value found for run_id: {run_id}"
            print(error_msg)
            self.update_state(
                state="FAILURE",
                meta={"status": error_msg, "run_id": run_id}
            )
            raise Exception(error_msg)

        print(f"Retrieved random value: {random_value}")

        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"status": "Generating password", "run_id": run_id}
        )

        # Simulate some processing time
        time.sleep(2)

        # Generate password of corresponding length
        password = generate_password_string(random_value)
        print(f"Generated password of length {random_value}: {password}")

        # Store password in database
        success = store_password(run_id, random_value, password)

        if success:
            print(f"🎉 Pipeline completed for run_id: {run_id}!")

            # Update task status
            self.update_state(
                state="SUCCESS",
                meta={
                    "status": "Password generated successfully",
                    "run_id": run_id,
                    "random_value": random_value,
                    "password": password
                }
            )

            return {
                "status": "success",
                "run_id": run_id,
                "random_value": random_value,
                "password": password
            }
        else:
            error_msg = "Failed to store password"
            print(error_msg)
            self.update_state(
                state="FAILURE",
                meta={"status": error_msg, "run_id": run_id}
            )
            raise Exception(error_msg)

    except Exception as e:
        print(f"Service 2 failed: {e}")
        self.update_state(
            state="FAILURE",
            meta={"status": f"Service 2 failed: {str(e)}", "run_id": run_id}
        )
        raise


def get_random_value(run_id: str):
    """Get the random value for a given run_id"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT random_value FROM tasks WHERE run_id = %s",
                (run_id,)
            )
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result and result[0]:
                return result[0]
            else:
                print(f"No random value found for run_id: {run_id}")
                return None
        except Exception as e:
            print(f"Error getting random value: {e}")
            return None
    else:
        print("Failed to connect to database")
        return None


def generate_password_string(length: int) -> str:
    """Generate a random password of specified length"""
    # Use letters, digits, and special characters
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(random.choice(characters) for _ in range(length))
    return password


def store_password(run_id: str, random_value: int, password: str) -> bool:
    """Store the generated password in the database"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO passwords (run_id, random_value, password) VALUES (%s, %s, %s)",
                (run_id, random_value, password)
            )
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Successfully stored password for run_id {run_id}")
            return True
        except Exception as e:
            print(f"Error storing password: {e}")
            return False
    else:
        print("Failed to connect to database")
        return False


@celery_app.task(bind=True, name="pipeline.run_complete_pipeline")
def run_complete_pipeline(self, run_id: str):
    """Run the complete pipeline: Service 1 -> Service 2 using task chaining"""
    try:
        print(f"🚀 Starting complete pipeline for run_id: {run_id}")

        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"status": "Starting pipeline", "run_id": run_id}
        )

        # Step 1: Generate random value
        print("Step 1: Generating random value...")
        self.update_state(
            state="PROGRESS",
            meta={"status": "Step 1: Generating random value", "run_id": run_id}
        )

        # Call Service 1 and wait for it to complete
        # We can't use .wait() or .get() from within a task, so we'll just return
        # The backend will need to handle the chaining
        service1_task = generate_random_value.delay(run_id)

        # Update task status to show Service 1 is running
        self.update_state(
            state="PROGRESS",
            meta={
                "status": "Step 1: Service 1 started",
                "run_id": run_id,
                "service1_task_id": service1_task.id
            }
        )

        print(f"Service 1 task started: {service1_task.id}")

        # Return the task ID so the backend can monitor it
        return {
            "status": "service1_started",
            "run_id": run_id,
            "service1_task_id": service1_task.id,
            "message": "Service 1 started. Monitor task status for completion."
        }

    except Exception as e:
        print(f"Pipeline failed: {e}")
        self.update_state(
            state="FAILURE",
            meta={"status": f"Pipeline failed: {str(e)}", "run_id": run_id}
        )
        raise


@celery_app.task(bind=True, name="pipeline.continue_pipeline")
def continue_pipeline(self, run_id: str, random_value: int):
    """Continue pipeline after Service 1 completes - called by Service 1 callback"""
    try:
        print(
            f"🔄 Continuing pipeline for run_id: {run_id} with random value: {random_value}")

        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"status": "Continuing pipeline",
                  "run_id": run_id, "random_value": random_value}
        )

        # Step 2: Generate password
        print("Step 2: Generating password...")
        self.update_state(
            state="PROGRESS",
            meta={"status": "Step 2: Generating password", "run_id": run_id}
        )

        # Call Service 2
        service2_task = generate_password.delay(run_id)

        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={
                "status": "Step 2: Service 2 started",
                "run_id": run_id,
                "service2_task_id": service2_task.id
            }
        )

        print(f"Service 2 task started: {service2_task.id}")

        return {
            "status": "service2_started",
            "run_id": run_id,
            "service2_task_id": service2_task.id,
            "message": "Service 2 started. Monitor task status for completion."
        }

    except Exception as e:
        print(f"Continue pipeline failed: {e}")
        self.update_state(
            state="FAILURE",
            meta={
                "status": f"Continue pipeline failed: {str(e)}", "run_id": run_id}
        )
        raise
