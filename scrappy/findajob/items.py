# Define custom item classes in your project

import scrapy


class LinkedInJobItem(scrapy.Item):
    job_id = scrapy.Field()
    job_title = scrapy.Field()
    employer = scrapy.Field()
    job_location = scrapy.Field()
    job_description = scrapy.Field()
    employment_type = scrapy.Field()
    job_function = scrapy.Field()
    seniority_level = scrapy.Field()
    job_url = scrapy.Field()
    employer_url = scrapy.Field()
    industries = scrapy.Field()
