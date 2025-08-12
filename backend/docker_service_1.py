#!/usr/bin/env python3
"""
Docker Service 1: Polls task queue and generates random values
"""
import psycopg2
import random
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


def get_pending_task():
    """Get a pending task from the queue for service_1"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()

            # Get the oldest pending task for service_1
            cursor.execute("""
                SELECT id, run_id FROM task_queue 
                WHERE service_name = 'service_1' AND status = 'pending'
                ORDER BY created_at ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            """)

            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result:
                return {"id": result[0], "run_id": result[1]}
            return None

        except Exception as e:
            print(f"Error getting pending task: {e}")
            return None
    return None


def mark_task_started(task_id: int):
    """Mark a task as started"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE task_queue SET status = 'processing', started_at = CURRENT_TIMESTAMP WHERE id = %s",
                (task_id,)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error marking task as started: {e}")
            return False
    return False


def mark_task_completed(task_id: int):
    """Mark a task as completed"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE task_queue SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = %s",
                (task_id,)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error marking task as completed: {e}")
            return False
    return False


def create_next_task(run_id: str):
    """Create the next task in the pipeline for service_2"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO task_queue (run_id, service_name) VALUES (%s, %s)",
                (run_id, "service_2")
            )
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Created next task for service_2 with run_id: {run_id}")
            return True
        except Exception as e:
            print(f"Error creating next task: {e}")
            return False
    return False


def process_task(task_id: int, run_id: str):
    """Process the task by generating a random value and storing it"""
    print(f"Processing task {task_id} for run_id: {run_id}")

    # Mark task as started
    if not mark_task_started(task_id):
        return False

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

            # Create next task for service_2
            create_next_task(run_id)

            # Mark task as completed
            mark_task_completed(task_id)

            return True
        except Exception as e:
            print(f"Error storing random value: {e}")
            return False
    else:
        print("Failed to connect to database")
        return False


def main():
    """Main function - continuously poll for tasks"""
    print("🚀 Starting Docker Service 1 (Random Value Generator)")
    print("📊 Polling task queue for new tasks...")

    while True:
        try:
            # Get pending task
            task = get_pending_task()

            if task:
                print(
                    f"🎯 Found pending task: {task['id']} for run_id: {task['run_id']}")

                # Process the task
                success = process_task(task['id'], task['run_id'])

                if success:
                    print(f"✅ Task {task['id']} completed successfully")
                else:
                    print(f"❌ Task {task['id']} failed")
            else:
                print("⏳ No pending tasks found, waiting...")

            # Wait before next poll
            time.sleep(5)

        except KeyboardInterrupt:
            print("\n🛑 Service 1 stopped by user")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            time.sleep(10)  # Wait longer on error


if __name__ == "__main__":
    main()
