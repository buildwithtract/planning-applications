from datetime import date, datetime, timedelta
from typing import Dict, Generator, List, Optional
from uuid import uuid4

import scrapy
from scrapy.http.request import Request
from scrapy.http.response import Response
from scrapy.http.response.text import TextResponse

from planning_applications.settings import DEFAULT_DATE_FORMAT
from planning_applications.spiders.base import BaseSpider


class NorthgateSpider(BaseSpider):
    domain = "planning.wandsworth.gov.uk"
    start_url = f"https://{domain}/Northgate/PlanningExplorer/GeneralSearch.aspx"
    allowed_domains = [domain]

    start_date: date
    end_date: date

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if isinstance(self.start_date, str):
            self.start_date = datetime.strptime(self.start_date, DEFAULT_DATE_FORMAT).date()

        if isinstance(self.end_date, str):
            self.end_date = datetime.strptime(self.end_date, DEFAULT_DATE_FORMAT).date()

        if self.start_date > self.end_date:
            raise ValueError(f"start_date {self.start_date} must be earlier than end_date {self.end_date}")

    def start_requests(self) -> Generator[Request, None, None]:
        """
        First entry point: load the initial page to get required cookies
        """
        session_id = str(uuid4())

        yield Request(
            self.start_url,
            callback=self._handle_cookies,
            errback=self.handle_error,
            dont_filter=True,
            cb_kwargs={"session_id": session_id},
            meta={"zyte_api_automap": {"session": {"id": session_id}}},  # Enable cookie handling
        )

    def _handle_cookies(self, response: TextResponse, session_id: str) -> Generator[Request, None, None]:
        """
        Handle the initial response and prepare the search request
        """
        # Extract ASP.NET form values
        viewstate = response.css("#__VIEWSTATE::attr(value)").get()
        viewstategenerator = response.css("#__VIEWSTATEGENERATOR::attr(value)").get()
        eventvalidation = response.css("#__EVENTVALIDATION::attr(value)").get()

        start_date = self.start_date.strftime("%d %B %Y")
        end_date = self.end_date.strftime("%d %B %Y")

        print(f"Searching for applications between {start_date} and {end_date}")

        # Form data that needs to be submitted
        formdata = {
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            "cboSelectDateValue": "1",  # This is for "Date Received"
            "rbGroup": "rbRange",  # This selects the date range option
            "dateStart": start_date,
            "dateEnd": end_date,
            "csbtnSearch": "Search",  # The search button
        }

        # First submit the search form
        yield scrapy.FormRequest.from_response(
            response,
            formdata=formdata,
            callback=self._parse_search_results,
            errback=self.handle_error,
            dont_filter=True,
            meta={"zyte_api_automap": {"session": {"id": session_id}}},
        )

    def _parse_search_results(self, response: TextResponse) -> None:
        """
        Parse the search results page
        """
        # For debugging, save the response
        with open("debug_response.html", "w", encoding="utf-8") as f:
            f.write(response.text)

        # Add your parsing logic here
        print("Response status:", response.status)
        print("Response URL:", response.url)
