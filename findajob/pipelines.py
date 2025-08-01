# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from w3lib.html import remove_tags
import re
import json


class LinkedInJobPipeline:
    """Pipeline to clean and process job items."""
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Define text fields that need cleaning
        text_fields = ['job_title', 'company_name', 'location', 'job_url', 'description']
        
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
            adapter['description'] = re.sub(r'[^\w\s]', '', adapter['description'])
            # Remove numbers
            adapter['description'] = re.sub(r'\d+', '', adapter['description'])
            # Tokenize the text (splitting it into a list of words)
            adapter['description'] = adapter['description'].split()
        
        return item


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
