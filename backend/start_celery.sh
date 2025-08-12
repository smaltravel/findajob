#!/bin/bash

# Start Celery worker for FindAJob pipeline
echo "🚀 Starting Celery worker..."

# Activate virtual environment
source /app/venv/bin/activate

# Start Celery worker
exec celery -A celery_app worker --loglevel=info --concurrency=2
