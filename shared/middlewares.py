import logging

import scrapy
from scrapy import signals

from shared.db import get_connection, get_cursor, upsert_scraper_run


class LogScraperRunMiddleware:
    def __init__(self):
        self.connection = get_connection()
        self.cursor = get_cursor(self.connection)
        self.logger = logging.getLogger(__name__)

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s

    def spider_closed(self, spider: scrapy.Spider):
        self.logger.debug(f"Logging scraper run for {spider.__class__.__name__}")

        if not spider.crawler.stats:
            return

        stats = spider.crawler.stats.get_stats() if spider.crawler.stats else {}
        spider_class = f"{spider.__class__.__module__}.{spider.__class__.__name__}"

        upsert_scraper_run(self.cursor, spider_class, stats)

        self.connection.commit()
        self.cursor.close()
        self.connection.close()
