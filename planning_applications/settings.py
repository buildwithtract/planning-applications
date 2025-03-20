# Scrapy settings for planning_applications project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import scrapy_colorlog

from planning_applications.utils import getenv, hasenv

SCRAPEOPS_API_KEY = getenv("SCRAPEOPS_API_KEY")
ZYTE_API_KEY = getenv("ZYTE_API_KEY")

scrapy_colorlog.install()

BOT_NAME = "planning_applications"

SPIDER_MODULES = ["planning_applications.spiders"]
NEWSPIDER_MODULE = "planning_applications.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = getenv("USER_AGENT") if hasenv("USER_AGENT") else "planning_applications"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = True
COOKIES_DEBUG = True

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
    "shared.middlewares.LogScraperRunMiddleware": 543,
}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    "scrapeops_scrapy.middleware.retry.RetryMiddleware": 550,
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,
    "scrapy.downloadermiddlewares.cookies.CookiesMiddleware": 700,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
EXTENSIONS = {
    #    "scrapy.extensions.telnet.TelnetConsole": None,
    "scrapeops_scrapy.extension.ScrapeOpsMonitor": 500,
}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "planning_applications.pipelines.IdoxPlanningApplicationPipeline": 200,
    "planning_applications.pipelines.S3FileDownloadPipeline": 300,
    "planning_applications.pipelines.PostgresPipeline": 400,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

DEFAULT_DATE_FORMAT = "%Y-%m-%d"

ADDONS = {
    "scrapy_zyte_api.Addon": 500,
}

ZYTE_API_EXPERIMENTAL_COOKIES_ENABLED = True

# LOG_FILE = "log.txt"
LOG_LEVEL = "DEBUG"

# FEEDS = {
#     "output/output.json": {
#         "format": "jsonlines",
#         "encoding": "utf8",
#         "indent": 4,
#     },
# }

# These settings make the search breadth-first instead of depth-first
DEPTH_PRIORITY = 1
SCHEDULER_DISK_QUEUE = "scrapy.squeues.PickleFifoDiskQueue"
SCHEDULER_MEMORY_QUEUE = "scrapy.squeues.FifoMemoryQueue"

DOWNLOAD_FILES = False
PLANNING_APPLICATIONS_BUCKET_NAME = getenv("PLANNING_APPLICATIONS_BUCKET_NAME") or None

RETRY_ENABLED = True
RETRY_DELAY = 5
RETRY_HTTP_CODES = [400, 408, 421, 429, 500, 502, 503, 504, 520, 521, 522, 524]
