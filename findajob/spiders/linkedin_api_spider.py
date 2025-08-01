import scrapy

class LinkedInApiSpider(scrapy.Spider):
    name = 'linkedin_api'
    
    def start_requests(self):
        print("This is an API call placeholder.")
        yield scrapy.Request(url='https://dummyurl.com', callback=self.parse)

# WARNING: Legal Risks and High Chance of Being Blocked
# This spider is for educational purposes only.
# Using it to scrape LinkedIn may violate their terms of
# service and lead to legal consequences, including
# temporary or permanent bans.
class LinkedInScrapingSpider(scrapy.Spider):
    name = 'linkedin_cautious_scrape'
    
    def parse(self, response):
        mock_jobs = [
            {
                'title': 'Software Engineer',
                'company': 'Tech Corp',
                'location': 'San Francisco, CA'
            },
            {
                'title': 'Data Scientist',
                'company': 'Data Inc',
                'location': 'New York, NY'
            }
        ]
        
        for job in mock_jobs:
            yield job
