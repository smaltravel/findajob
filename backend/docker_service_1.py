#!/usr/bin/env python3
"""
Docker Service 1: Generates a random value and stores it in PostgreSQL
"""
import psycopg2
import random
import sys
import os
import time

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


def process_task(run_id):
    """Process the task by generating a random value and storing it"""
    print(f"Processing task for run_id: {run_id}")

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
            return True
        except Exception as e:
            print(f"Error storing random value: {e}")
            return False
    else:
        print("Failed to connect to database")
        return False


def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python docker_service_1.py <run_id>")
        sys.exit(1)

    run_id = sys.argv[1]
    print(f"Starting Docker Service 1 for run_id: {run_id}")

    # Simulate some processing time
    time.sleep(2)

    # Process the task
    success = process_task(run_id)

    if success:
        print("Task completed successfully")
        sys.exit(0)
    else:
        print("Task failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
