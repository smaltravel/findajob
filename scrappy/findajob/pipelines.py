# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from w3lib.html import remove_tags
import re
import json
import sqlite3
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


class DatabasePipeline:
    """Pipeline to store processed job items in a database."""

    def __init__(self):
        # Create database in the webapp directory for easy access
        webapp_dir = os.path.join(os.path.dirname(__file__), '..', 'webapp')
        os.makedirs(webapp_dir, exist_ok=True)
        db_path = os.path.join(webapp_dir, 'jobs.db')
        
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

        # Create table if it doesn't exist
        self.create_table_if_not_exists()

    def create_table_if_not_exists(self):
        """Create the 'jobs' table if it doesn't exist."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE,
                job_title TEXT,
                job_location TEXT,
                job_url TEXT,
                job_description TEXT,
                employer TEXT,
                employer_url TEXT,
                employment_type TEXT,
                job_function TEXT,
                seniority_level TEXT,
                industries TEXT,
                status TEXT NOT NULL CHECK (status IN ('new', 'user_rejected', 'filter_rejected', 'applied', 'interview_scheduled', 'interview_completed', 'offer_received', 'offer_accepted', 'offer_rejected', 'not_answered', 'employer_rejected')),
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_modified DATETIME DEFAULT CURRENT_TIMESTAMP
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
        
        self.conn.commit()

    def open_spider(self, spider):
        # Perform initialization tasks at the start of the spider.
        # Ensure the table is created when the spider opens
        self.create_table_if_not_exists()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        now = datetime.datetime.now().replace(microsecond=0).isoformat()

        # Check if the item already exists in the database
        self.cursor.execute(
            'SELECT 1 FROM jobs WHERE job_id=?', (adapter['job_id'],))
        if self.cursor.fetchone():
            spider.logger.info(
                f"Item with job_id {adapter['job_id']} already exists. Skipping insertion.")
            return item

        values = (
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
            'new',
            now,
            now,
        )
        self.cursor.execute('''
            INSERT INTO jobs (
                job_id, job_title, job_location, job_url, job_description,
                employer, employer_url, employment_type,
                job_function, seniority_level, industries, status,
                create_time, last_modified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', values)
        self.conn.commit()
        
        spider.logger.info(f"Inserted job: {adapter['job_title']} at {adapter['employer']}")
        return item

    def close_spider(self, spider):
        # Get count of jobs inserted in this session
        self.cursor.execute('''
            SELECT COUNT(*) FROM jobs 
            WHERE keywords = ? AND location = ? AND created_at >= datetime('now', '-1 hour')
        ''', (self.keywords, self.location))
        count = self.cursor.fetchone()[0]
        
        spider.logger.info(f"Spider finished. Inserted {count} new jobs")
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
