import re
import time
import scrapy
from urllib.parse import urlencode


class LinkedInSpider(scrapy.Spider):
    """
    A Scrapy spider to scrape job listings from a LinkedIn search page.
    This spider extracts job title, company name, and location from each job card.
    It also includes logic to count total jobs and a placeholder for pagination.
    """
    name = 'linkedin'
    base_search_url = 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search'
    base_job_url = 'https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/'

    def __init__(self, keywords: str, location: str, *args, **kwargs):
        super(LinkedInSpider).__init__(*args, **kwargs)
        # For more info visit: https://gist.github.com/Diegiwg/51c22fa7ec9d92ed9b5d1f537b9e1107
        self.__params = {
            'keywords': keywords,
            'location': location,
            # 'f_PP': '106772406', # Filter for jobs in a specific City. Accepts the $ID of the city
            'f_TPR': 'r86400',  # Filter for the time since the job was posted.
            'start': 0,
        }

    async def start(self):
        """
        The initial entry point for the spider. It constructs the search URL
        using the keywords and location, then sends a request to LinkedIn.
        """
        url = f'{self.base_search_url}?{urlencode(self.__params)}'
        self.log(f"Starting request for URL: {url}")
        yield scrapy.Request(
            url=url,
            callback=self.parse_search,
        )

    def parse_search(self, response):
        """
        Parses the search results page to get the links to individual job cards.
        """
        self.log("Parsing search results page...")

        cnt = 0

        # Walk whrought all job posting's data-entity-urn to get the jobPosting
        for job_badge in response.xpath('//html/body/li'):
            job_urn = job_badge.css(
                'div.base-card::attr(data-entity-urn)').get()
            # TODO: debug purposes
            if cnt > 3:
                break
            if job_urn:
                job_id = job_urn.split(':')[-1]
                cnt += 1
                self.log(f"Found job ID: {job_id}")

                # Yield a request to process the job card with the ID
                yield scrapy.Request(f'{self.base_job_url}{job_id}', callback=self.parse_job)

    def parse_job(self, response):
        """
        Parses a single detailed job page to extract all specified data.
        This function is called for each job URL found on the search results page.
        """
        self.log(f"Processing detailed job page: {response.url}")

        path_parsers = {
            '//html/body/section': LinkedInSpider.__parse_job_header,
            '//html/body/div': LinkedInSpider.__parse_job_summary,
        }

        data = dict()

        for path, handler in path_parsers.items():
            data = data | handler(response.xpath(path))

        # Yield the extracted data as a dictionary
        yield data

    @staticmethod
    def __parse_line(line: str):
        return ' '.join(l.rstrip() for l in line.split() if len(l) > 0)

    @staticmethod
    def __parse_job_header(card):
        job_a = card.xpath('//div/div[1]/div/a')
        employer_div = card.xpath('//div/div[1]/div/h4/div[1]')
        return {
            'job_title': LinkedInSpider.__parse_line(job_a.css('h2::text').get()),
            'job_url': LinkedInSpider.__parse_line(job_a.css('a::attr(href)').get()),
            'job_location': LinkedInSpider.__parse_line(employer_div.css('span.topcard__flavor--bullet::text').get()),
            'employer': LinkedInSpider.__parse_line(employer_div.css('a.topcard__org-name-link::text').get()),
            'employer_url': LinkedInSpider.__parse_line(employer_div.css('a.topcard__org-name-link::attr(href)').get()),
        }

    @staticmethod
    def __parse_job_summary(card):
        return {
            'job_description': LinkedInSpider.__parse_line(card.css('div.show-more-less-html__markup').get()),
            'seniority_level': LinkedInSpider.__parse_line(card.xpath('//section[1]/div/ul/li[1]/span/text()').get()),
            'employment_type': LinkedInSpider.__parse_line(card.xpath('//section[1]/div/ul/li[2]/span/text()').get()),
            'job_function': LinkedInSpider.__parse_line(card.xpath('//section[1]/div/ul/li[3]/span/text()').get()),
            'industries': LinkedInSpider.__parse_line(card.xpath('//section[1]/div/ul/li[4]/span/text()').get()),
        }
