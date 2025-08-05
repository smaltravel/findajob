"""
Configuration settings for the job processor tools.
"""

import os

# Database settings
DEFAULT_DATABASE_PATH = "../webapp/jobs.db"

# LLM API settings
DEFAULT_LLM_URL = "http://localhost:11434/api/generate"
DEFAULT_LLM_MODEL = "hr-consultant"

# Output settings
CV_OUTPUT_DIR = "generated_cvs"
COVER_LETTER_OUTPUT_DIR = "generated_cover_letters"

# Processing settings
REQUEST_TIMEOUT = 120  # seconds
DELAY_BETWEEN_REQUESTS = 1  # seconds

# File naming settings
CV_FILENAME_TEMPLATE = "CV_{job_title}_{company}_{timestamp}.docx"
COVER_LETTER_FILENAME_TEMPLATE = "CoverLetter_{job_title}_{company}_{timestamp}.txt"

# Database table names
JOBS_TABLE = "jobs"
PROCESSED_JOBS_TABLE = "processed_jobs"

# Processing status values
STATUS_PENDING = "pending"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

# Ensure output directories exist


def ensure_output_directories():
    """Create output directories if they don't exist."""
    os.makedirs(CV_OUTPUT_DIR, exist_ok=True)
    os.makedirs(COVER_LETTER_OUTPUT_DIR, exist_ok=True)
