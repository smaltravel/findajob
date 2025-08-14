#!/usr/bin/env python3
"""
Job Processor Tool

This script reads job records from the database by runid, processes them with a local LLM
to generate CVs, cover letters, and job summaries, and stores the results in a new table.

Usage:
    python job_processor.py --runid <runid> --cv_json <path> [--database <path>]
"""

import argparse
import sqlite3
import json
import os
import sys
from datetime import datetime
from typing import Dict, List
import logging
from providers import AIProvider, OllamaProvider, GoogleAIProvider, AIProviderConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JobProcessor:
    """Processes job records and generates CVs, cover letters, and summaries using a local LLM."""

    def __init__(self, database_path: str, ai_provider: AIProvider):
        """
        Initialize the JobProcessor.

        Args:
            database_path: Path to the SQLite database
            llm_url: URL of the local LLM API (default: Ollama)
        """
        self.database_path = database_path
        self.ai_provider = ai_provider
        self.conn = None
        self.cursor = None

    def connect_database(self):
        """Connect to the SQLite database and create necessary tables."""
        try:
            self.conn = sqlite3.connect(self.database_path)
            self.cursor = self.conn.cursor()
            self._create_processed_jobs_table()
            logger.info(f"Connected to database: {self.database_path}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def _create_processed_jobs_table(self):
        """Create the processed_jobs table if it doesn't exist."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                runid TEXT NOT NULL,
                cover_letter TEXT,
                job_summary TEXT,
                processing_status TEXT DEFAULT 'pending',
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES jobs (id)
            )
        ''')

        # Create indexes for better performance
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_processed_jobs_runid ON processed_jobs(runid)
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_processed_jobs_status ON processed_jobs(processing_status)
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_processed_jobs_job_id ON processed_jobs(job_id)
        ''')

        self.conn.commit()
        logger.info("Created processed_jobs table and indexes")

    def get_new_jobs_by_runid(self, runid: str) -> List[Dict]:
        """
        Get all new job records for the given runid that haven't been processed yet.

        Args:
            runid: The run ID to filter jobs by

        Returns:
            List of job records as dictionaries
        """
        query = '''
            SELECT j.* FROM jobs j
            LEFT JOIN processed_jobs pj ON j.id = pj.job_id
            WHERE j.runid = ? AND pj.job_id IS NULL
            ORDER BY j.created_at ASC
        '''

        self.cursor.execute(query, (runid,))
        jobs = self.cursor.fetchall()

        # Get column names
        columns = [description[0] for description in self.cursor.description]

        # Convert to list of dictionaries
        job_records = []
        for job in jobs:
            job_dict = dict(zip(columns, job))
            job_records.append(job_dict)

        logger.info(f"Found {len(job_records)} new jobs for runid: {runid}")
        return job_records

    def process_job(self, job_data: Dict) -> Dict:
        """
        Process a single job record to generate CV, cover letter, and summary.

        Args:
            job_data: Job record data

        Returns:
            Dictionary containing generated content and file paths
        """
        job_id = job_data['id']
        runid = job_data['runid']

        logger.info(
            f"Processing job {job_id}: {job_data.get('job_title')} at {job_data.get('employer')}")

        try:
            # Update context for the current job
            self.ai_provider.set_job(job_data)

            # Generate cover letter
            logger.info("Generating cover letter")
            cover_letter = self.ai_provider.cover_letter()

            # Generate job summary
            logger.info("Generating job summary")
            job_summary = self.ai_provider.job_description()

            return {
                'job_id': job_id,
                'runid': runid,
                'cover_letter': cover_letter,
                'job_summary': job_summary,
                'processing_status': 'completed',
                'error_message': None
            }

        except Exception as e:
            logger.error(f"Failed to process job {job_id}: {e}")
            return {
                'job_id': job_id,
                'runid': runid,
                'cover_letter': None,
                'job_summary': None,
                'processing_status': 'failed',
                'error_message': str(e)
            }

    def save_processed_job(self, processed_data: Dict):
        """Save processed job data to the database."""
        values = (
            processed_data['job_id'],
            processed_data['runid'],
            processed_data['cover_letter'],
            processed_data['job_summary'],
            processed_data['processing_status'],
            processed_data['error_message'],
            datetime.now().isoformat()
        )
        query = '''
            INSERT INTO processed_jobs (
                job_id, runid, cover_letter, job_summary, processing_status, error_message, updated_at
            )
        ''' + str(' VALUES (%s)' % (', '.join(['?' for _ in values])))

        self.cursor.execute(query, values)
        self.conn.commit()

        logger.info(
            f"Saved processed job {processed_data['job_id']} to database")

    def process_jobs_by_runid(self, runid: str):
        """
        Process all new jobs for the given runid.

        Args:
            runid: The run ID to process jobs for
        """
        logger.info(f"Starting to process jobs for runid: {runid}")

        # Get new jobs
        jobs = self.get_new_jobs_by_runid(runid)

        if not jobs:
            logger.info(f"No new jobs found for runid: {runid}")
            return

        # Process each job
        for i, job in enumerate(jobs, 1):
            logger.info(f"Processing job {i}/{len(jobs)}")

            processed_data = self.process_job(job)
            self.save_processed_job(processed_data)

            # Add a small delay between requests to be respectful to the LLM API
            import time
            time.sleep(1)

        logger.info(
            f"Completed processing {len(jobs)} jobs for runid: {runid}")

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


def main():
    """Main function to run the job processor."""
    parser = argparse.ArgumentParser(
        description='Process job records and generate CVs, cover letters, and summaries')
    parser.add_argument('--runid', required=True,
                        help='Run ID to process jobs for')
    parser.add_argument('--database', default='../webapp/jobs.db',
                        help='Path to the SQLite database (default: ../webapp/jobs.db)')
    parser.add_argument('--cv_json', required=True,
                        help='Path to the user CV JSON file')
    parser.add_argument('--provider', choices=['ollama', 'google'], default='ollama',
                        help='AI provider to use (default: ollama)')
    parser.add_argument('--api_key',
                        help='API key for Google AI (required if provider is google)')

    args = parser.parse_args()

    # Check if database exists
    if not os.path.exists(args.database):
        logger.error(f"Database file not found: {args.database}")
        sys.exit(1)

    # Load CV data
    with open(args.cv_json, 'r') as f:
        cv_data = json.load(f)

    # Initialize AI provider based on choice
    if args.provider == 'ollama':
        ai_provider = OllamaProvider(
            AIProviderConfig(
                model="deepseek-r1:7b",
                base_url="http://localhost:11434",
                user_cv=cv_data
            )
        )
    elif args.provider == 'google':
        if not args.api_key:
            logger.error("API key is required for Google AI provider")
            sys.exit(1)
        ai_provider = GoogleAIProvider(
            AIProviderConfig(
                model="gemini-2.5-flash-lite",
                api_key=args.api_key,
                user_cv=cv_data
            )
        )
    else:
        logger.error(f"Unknown provider: {args.provider}")
        sys.exit(1)

    # Initialize processor
    processor = JobProcessor(args.database, ai_provider)

    try:
        # Connect to database
        processor.connect_database()

        # Process jobs
        processor.process_jobs_by_runid(args.runid)

        logger.info("Job processing completed successfully")

    except Exception as e:
        logger.error(f"Job processing failed: {e}")
        sys.exit(1)
    finally:
        processor.close()


if __name__ == "__main__":
    main()
