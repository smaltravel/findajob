import scrapy
import re
from datetime import datetime, timedelta

class StepstoneSpider(scrapy.Spider):
    name = "stepstone"
    allowed_domains = ["stepstone.de"]

    def __init__(self, role="data-analyst", city="frankfurt-am-main", radius=30, *args, **kwargs):
        super(StepstoneSpider, self).__init__(*args, **kwargs)
        self.start_urls = [
            f"https://www.stepstone.de/jobs/{role}/in-{city}?radius={radius}"
        ]
        self.__projessed_jobs = 0

    def parse(self, response):
        for job in response.css('a[data-testid="job-item-title"]::attr(href)').getall():
            url = response.urljoin(job)
            yield scrapy.Request(url, callback=self.parse_job)

        if self.__projessed_jobs > 10:
            return

        next_page = response.css('a[aria-label="Nächste"]::attr(href)').get()
        if next_page:
            yield scrapy.Request(response.urljoin(next_page), callback=self.parse)

    def parse_posted_date(self, text):
        text = text.lower()

        if "heute" in text:
            return datetime.today().date()

        if "gestern" in text:
            return (datetime.today() - timedelta(days=1)).date()

        match = re.search(r"vor\s+(\d+)\s+tagen", text)
        if match:
            days_ago = int(match.group(1))
            return (datetime.today() - timedelta(days=days_ago)).date()

        return None


    def parse_job(self, response):
        if self.__projessed_jobs > 10:
            return
        self.log("Processing url: " + response.url)
        date_text_raw = response.css(
            'li.at-listing__list-icons_date span.job-ad-display-du9bhi span::text'
        ).get()
        date_text = date_text_raw.strip() if date_text_raw else ""

        role = response.css('h1[data-at="header-job-title"]::text').get()
        company_list = response.css('span[data-at="metadata-company-name"] *::text').getall()
        company = company_list[-1].strip() if company_list else None
        location = response.css('li.at-listing__list-icons_location span[data-genesis-element="TEXT"] span::text').get()
        description_list = response.css('div[data-at="section-text-description-content"] li::text').getall()
        description = " ".join([d.strip() for d in description_list]) if description_list else None

        self.__projessed_jobs += 1

        yield {
            "role": role,
            "company": company,
            "location": location,
            "description": description,
            # "level": response.xpath("//strong[contains(text(), 'Junior') or contains(text(),'Senior') or contains(text(),'Middle')]/text()").get(default=""),
            "url": response.url,
            "date_posted": self.parse_posted_date(date_text)
        }

        
