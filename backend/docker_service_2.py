#!/usr/bin/env python3
"""
Docker Service 2: Reads random value and generates password of corresponding length
"""
import psycopg2
import random
import string
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


def get_random_value(run_id):
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


def store_password(run_id, random_value, password):
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


def process_task(run_id):
    """Process the task by reading random value and generating password"""
    print(f"Processing task for run_id: {run_id}")

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

    return success


def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python docker_service_2.py <run_id>")
        sys.exit(1)

    run_id = sys.argv[1]
    print(f"Starting Docker Service 2 for run_id: {run_id}")

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
