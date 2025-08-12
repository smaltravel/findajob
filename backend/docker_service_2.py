#!/usr/bin/env python3
"""
Docker Service 2: Polls task queue and generates passwords
"""
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


def get_pending_task():
    """Get a pending task from the queue for service_2"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()

            # Get the oldest pending task for service_2
            cursor.execute("""
                SELECT id, run_id FROM task_queue 
                WHERE service_name = 'service_2' AND status = 'pending'
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


def generate_password(length):
    """Generate a random password of specified length"""
    # Use letters, digits, and special characters
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(random.choice(characters) for _ in range(length))
    return password


def store_password(run_id: str, random_value: int, password: str):
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


def process_task(task_id: int, run_id: str):
    """Process the task by reading random value and generating password"""
    print(f"Processing task {task_id} for run_id: {run_id}")

    # Mark task as started
    if not mark_task_started(task_id):
        return False

    # Get the random value
    random_value = get_random_value(run_id)
    if random_value is None:
        return False

    print(f"Retrieved random value: {random_value}")

    # Generate password of corresponding length
    password = generate_password(random_value)
    print(f"Generated password of length {random_value}: {password}")

    # Store password in database
    success = store_password(run_id, random_value, password)

    if success:
        # Mark task as completed
        mark_task_completed(task_id)
        print(f"🎉 Pipeline completed for run_id: {run_id}!")
        print(f"📧 User should be notified that pipeline is complete")

    return success


def main():
    """Main function - continuously poll for tasks"""
    print("🔐 Starting Docker Service 2 (Password Generator)")
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
            print("\n🛑 Service 2 stopped by user")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            time.sleep(10)  # Wait longer on error


if __name__ == "__main__":
    main()
