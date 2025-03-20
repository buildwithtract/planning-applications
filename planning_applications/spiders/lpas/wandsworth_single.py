from datetime import datetime

import scrapy
from parsel import Selector


class WandsworthSingleSpider(scrapy.Spider):
    name = "wandsworth_single"
    allowed_domains = ["planning.wandsworth.gov.uk"]
    start_urls = [
        "https://planning.wandsworth.gov.uk/Northgate/PlanningExplorer/Generic/StdDetails.aspx?PT=Planning%20Applications%20On-Line&TYPE=PL/PlanningPK.xml&PARAM0=1140089&XSLT=/Northgate/PlanningExplorer/SiteFiles/Skins/Wandsworth/xslt/PL/PLDetails.xslt&FT=Planning%20Application%20Details&PUBLIC=Y&XMLSIDE=&DAURI=PLANNING"
    ]
    not_yet_working = True

    # Define our special rows, and which handler needs to be used
    special_rows = {
        "Application Registered": "date",
        "Comments Until": "date",
        "Date of Committee": "date",
        "Decision": "status_plus_date",
        "Appeal Lodged": "date",
        "Location Co ordinates": "easting_northing",
    }

    # define our special handlers
    special_handlers = {
        "date": lambda self, row: self._handle_date(row),
        "status_plus_date": lambda self, row: self._handle_status_plus_date(row),
        "easting_northing": lambda self, row: self._handle_easting_northing(row),
    }

    def __init__(self, url=None, *args, **kwargs):
        super(WandsworthSingleSpider, self).__init__(*args, **kwargs)
        # Ensure the URL is passed
        if url:
            self.start_urls = [url]

    def parse(self, response):
        application_details = {}

        for dataview in response.xpath('//div[@class="dataview"]'):
            # Get the table heading (h1)
            heading = dataview.xpath("h1/text()").get().split("\xa0")[0]
            # Split the string on the non-breaking space character - everything before spaces is consistent
            application_details[heading] = self._parse_dataview(dataview)

        print(application_details)

    def _parse_dataview(self, dataview) -> dict:
        dataview_parsed = {}

        # Work through every row in the table
        for row in dataview.xpath("ul/li"):
            # The text in the span is the table row name
            row_name = row.xpath("div/span/text()").get()
            # If we need to do something special about this row, do it
            if row_name in self.special_rows:
                handler = self.special_handlers.get(self.special_rows[row_name])
                if handler:
                    row_value = handler(self, row)
                else:
                    self.logger.error(f"No handler for {row_name}")
                    return {}
            else:
                # The text in the div and outside of the span is the row value, plus some unprinted stuff
                #    - we only want the div text
                row_value = row.xpath("div/text()")[1].get().split("\xa0")[0]
                # When we've finished parsing, or if we haven't parsed, store
                dataview_parsed[row_name] = row_value

        return dataview_parsed

        # handler = self.handlers.get(dataview.xpath('h1/text()').get().split('\xa0')[0])
        if handler:
            return handler(self, dataview)

    def _handle_date(self, row: Selector) -> datetime | str:
        ### Handle DATE-ONLY rows - not status+date
        date_string = row.xpath("div/text()")[1].get().split("\xa0")[0]
        try:
            return datetime.strptime(date_string, "%d/%m/%Y")
        except Exception:
            return f"error parsing date: got {date_string}"

    def _handle_status_plus_date(self, row: Selector) -> dict:
        ### Handle STATUS+DATE rows
        [status, date_string] = row.xpath("div/text()")[1].get().split("\xa0")
        try:
            date = datetime.strptime(date_string.strip(), "%d/%m/%Y")
        except Exception:
            date = f"error parsing date: got {date_string}"
        return {"status": status, "date": date}

    def _handle_easting_northing(self, row: Selector) -> dict:
        ### Handle EASTING/NORTHING (UK grid coordinates) rows
        # Easting/Northing is on the 15th "ul/li" row
        # Received as a list ['Easting', '530014', 'Northing', '177704', '']
        [_, easting, _, northing, _] = row.xpath("div/text()")[1].get().split("\xa0")
        return {"easting": easting, "northing": northing}

    # def _parse_heading(self, dataview) -> dict:

    # def _parse_application_progress_summary(self, dataview) -> dict:

    # def _parse_application_details(self, dataview) -> dict:

    # def _parse_other_information(self, dataview) -> dict:


# to do: parse comments as well (separate page)
# TODO -- Grab the planning application documents (including comments) PDFs. Link is always https://planning2.wandsworth.gov.uk/planningcase/comments.aspx?case=$APPLICATION_NUMBER
#       -- The documents page runs on JS, so that's annoying. Can we reverse engineer the API?
#       -- For now, we'
