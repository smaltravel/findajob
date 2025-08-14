from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.signalmanager import dispatcher
from app.celery import celery_app
from app.schemas.search import SpiderConfig
from app.core.spiders.linkedin_api_spider import LinkedInSpider

@celery_app.task
def crawl_jobs(config: SpiderConfig, run_id: str):
    """
    Crawl jobs from the web using Scrapy.
    """
    jobs = []

    def crawler_results(signal, sender, item, response, spider):
        jobs.append(item)

    dispatcher.connect(crawler_results, signal=signals.item_scraped)

    process = CrawlerProcess(settings={
        "LOG_LEVEL": "INFO",
        "BOT_NAME": "findajob",
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_DELAY": 1,
        "FEED_EXPORT_ENCODING": "utf-8",
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    })
    process.crawl(LinkedInSpider, **config.model_dump(), run_id=run_id)
    process.start()
