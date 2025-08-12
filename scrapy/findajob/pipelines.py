# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from w3lib.html import remove_tags
import re
import json
import psycopg2
import datetime
import os


class LinkedInJobPipeline:
    """Pipeline to clean and process job items."""

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # Define text fields that need cleaning
        text_fields = ['job_title', 'company_name',
                       'location', 'job_url', 'description']

        for field in text_fields:
            if field in adapter and isinstance(adapter[field], str):
                # Convert to lowercase
                adapter[field] = adapter[field].lower()
                # Remove leading and trailing whitespace
                adapter[field] = adapter[field].strip()
                # Remove common HTML tags from description
                if field == 'description':
                    adapter[field] = remove_tags(adapter[field])

        # Prepare the item for AI model
        self.prepare_for_ai_model(item)

        return item

    def prepare_for_ai_model(self, item):
        """
        Preprocesses the description text for an AI model.

        Args:
            item (dict): The job item with a 'description' field to preprocess.

        Returns:
            dict: The modified item with the processed description.
        """
        adapter = ItemAdapter(item)

        if 'description' in adapter and isinstance(adapter['description'], str):
            # Remove punctuation
            adapter['description'] = re.sub(
                r'[^\w\s]', '', adapter['description'])
            # Remove numbers
            adapter['description'] = re.sub(r'\d+', '', adapter['description'])
            # Tokenize the text (splitting it into a list of words)
            adapter['description'] = adapter['description'].split()

        return item


class PostgresqlPipeline:
    """Pipeline to store processed job items in a PostgreSQL database."""

    def __init__(self, db_host=None, db_name=None, db_user=None, db_password=None, db_port=None):
        # Get database connection parameters from settings or use defaults
        from scrapy.utils.project import get_project_settings
        settings = get_project_settings()

        self.db_host = db_host or settings.get('POSTGRES_HOST', 'postgres')
        self.db_name = db_name or settings.get('POSTGRES_DB', 'findajob')
        self.db_user = db_user or settings.get('POSTGRES_USER', 'postgres')
        self.db_password = db_password or settings.get(
            'POSTGRES_PASSWORD', 'password')
        self.db_port = db_port or settings.get('POSTGRES_PORT', '5432')

        self.conn = None
        self.cursor = None

    def connect(self):
        """Establish connection to PostgreSQL database."""
        try:
            self.conn = psycopg2.connect(
                host=self.db_host,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                port=self.db_port
            )
            self.cursor = self.conn.cursor()
            self.conn.autocommit = False
        except psycopg2.Error as e:
            raise Exception(f"Failed to connect to PostgreSQL: {e}")

    def create_table_if_not_exists(self):
        """Create the 'jobs' table if it doesn't exist."""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id SERIAL PRIMARY KEY,
                    spider_source VARCHAR(255) NOT NULL,
                    job_id VARCHAR(255) UNIQUE,
                    job_title TEXT,
                    job_location TEXT,
                    job_url TEXT,
                    job_description TEXT,
                    employer VARCHAR(255),
                    employer_url TEXT,
                    employment_type VARCHAR(100),
                    job_function VARCHAR(255),
                    seniority_level VARCHAR(100),
                    industries TEXT,
                    run_id VARCHAR(255) REFERENCES tasks(run_id),
                    status VARCHAR(50) NOT NULL DEFAULT 'new',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create index for better query performance
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_job_id ON jobs(job_id)
            ''')
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_status ON jobs(status)
            ''')
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_created_at ON jobs(created_at)
            ''')
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_job_title ON jobs(job_title)
            ''')
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_employer ON jobs(employer)
            ''')
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_run_id ON jobs(run_id)
            ''')

            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception(f"Failed to create table: {e}")

    def open_spider(self, spider):
        """Perform initialization tasks at the start of the spider."""
        self.connect()
        self.create_table_if_not_exists()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        now = datetime.datetime.now().replace(microsecond=0).isoformat()

        try:
            # Check if the item already exists in the database
            self.cursor.execute(
                'SELECT 1 FROM jobs WHERE job_id = %s', (adapter['job_id'],))
            if self.cursor.fetchone():
                spider.logger.info(
                    f"Item with job_id {adapter['job_id']} already exists. Skipping insertion.")
                return item

            # Insert new job
            self.cursor.execute('''
                INSERT INTO jobs (
                    spider_source,
                    job_id,
                    job_title,
                    job_location,
                    job_url,
                    job_description,
                    employer,
                    employer_url,
                    employment_type,
                    job_function,
                    seniority_level,
                    industries,
                    run_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                spider.name,
                adapter['job_id'],
                adapter['job_title'],
                adapter['job_location'],
                adapter['job_url'],
                adapter['job_description'],
                adapter['employer'],
                adapter['employer_url'],
                adapter['employment_type'],
                adapter['job_function'],
                adapter['seniority_level'],
                adapter['industries'],
                adapter.get('run_id', '')
            ))

            self.conn.commit()

            spider.logger.info(
                f"Inserted job: {adapter['job_title']} at {adapter['employer']} with run_id: {adapter.get('run_id', 'N/A')}")
            return item

        except psycopg2.Error as e:
            self.conn.rollback()
            spider.logger.error(f"Database error: {e}")
            raise e

    def close_spider(self, spider):
        """Close database connection when spider finishes."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


class SaveToFilePipeline:
    """Pipeline to save processed job items to a JSON Lines file."""

    def __init__(self):
        self.file = open('processed_jobs.jsonl', 'w')

    def process_item(self, item, spider):
        # Write the cleaned item as a single line in JSON format
        json.dump(item, self.file)
        self.file.write('\n')
        return item

    def close_spider(self, spider):
        # Close the file when the spider finishes
        self.file.close()
