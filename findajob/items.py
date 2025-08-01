# Define custom item classes in your project

import scrapy

class LinkedInJobItem(scrapy.Item):
    title = scrapy.Field()
    company = scrapy.Field()
    location = scrapy.Field()
    description = scrapy.Field()
    salary = scrapy.Field()
    url = scrapy.Field()
