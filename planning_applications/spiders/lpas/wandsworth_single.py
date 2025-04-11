import json
from datetime import datetime

import scrapy
from pyproj import Transformer
from rich import print
from scrapy.http.request import Request

from planning_applications.items import NorthgatePlanningApplication


class WandsworthSingleSpider(scrapy.Spider):
    name = "wandsworth_single"
    allowed_domains = ["planning.wandsworth.gov.uk"]
    start_urls = [
        "https://planning.wandsworth.gov.uk/Northgate/PlanningExplorer/Generic/StdDetails.aspx?PT=Planning%20Applications%20On-Line&TYPE=PL/PlanningPK.xml&PARAM0=1140089&XSLT=/Northgate/PlanningExplorer/SiteFiles/Skins/Wandsworth/xslt/PL/PLDetails.xslt&FT=Planning%20Application%20Details&PUBLIC=Y&XMLSIDE=&DAURI=PLANNING"
    ]
    not_yet_working = True

    # Create transformer for UK National Grid to WGS84
    transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)

    def __init__(self, url=None, *args, **kwargs):
        super(WandsworthSingleSpider, self).__init__(*args, **kwargs)
        if url:
            self.start_urls = [url]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, callback=self.parse)

    def parse(self, response):
        planning_application = NorthgatePlanningApplication(lpa="wandsworth", url=self.start_urls[0])

        # Map of attribute names to XPath expressions and optional transform functions
        field_mappings = {
            "application_registered": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Application Registered"]]/text()[2]',
                "transform": self._transform_date,
            },
            "comments_until": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Comments Until"]]/text()[2]',
                "transform": self._transform_date,
            },
            "date_of_committee": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Date of Committee"]]/text()[2]',
                "transform": self._transform_date,
            },
            "decision": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Decision"]]/text()[2]',
                "transform": self._extract_decision_status,
            },
            "decision_date": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Decision"]]/text()[2]',
                "transform": self._extract_decision_date,
            },
            "appeal_lodged": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Appeal Lodged"]]/text()[2]',
                "transform": self._transform_date,
            },
            "appeal_decision": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Appeal Decision"]]/text()[2]',
                "transform": lambda x: x.strip() if x else None,
            },
            "application_number": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Application Number"]]/text()[2]',
                "transform": lambda x: x.strip() if x else None,
            },
            "site_address": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Site Address"]]/text()[2]',
                "transform": lambda x: x.strip() if x else None,
            },
            "application_type": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Application Type"]]/text()[2]',
                "transform": lambda x: x.strip() if x else None,
            },
            "development_type": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Development Type"]]/text()[2]',
                "transform": lambda x: x.strip() if x else None,
            },
            "proposal": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Proposal"]]/text()[2]',
                "transform": lambda x: x.strip() if x else None,
            },
            "current_status": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Current Status"]]/text()[2]',
                "transform": lambda x: x.strip() if x else None,
            },
            "applicant": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Applicant"]]/text()[2]',
                "transform": lambda x: x.strip() if x else None,
            },
            "agent": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Agent"]]/text()[2]',
                "transform": lambda x: x.strip() if x else None,
            },
            "wards": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Wards"]]/text()[2]',
                "transform": lambda x: x.strip() if x else None,
            },
            "location_coordinates": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Location Co ordinates"]]/text()[2]',
                "transform": self._transform_easting_northing,
            },
            "parishes": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Parishes"]]/text()[2]',
                "transform": lambda x: x.strip() if x else None,
            },
            "os_mapsheet": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="OS Mapsheet"]]/text()[2]',
                "transform": lambda x: x.strip() if x else None,
            },
            "appeal_submitted": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Appeal Submitted?"]]/text()[2]',
                "transform": lambda x: x.strip() if x else None,
            },
            "case_officer": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Case Officer / Tel"]]/text()[2]',
                "transform": lambda x: x.strip() if x else None,
            },
            "division": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Division"]]/text()[2]',
                "transform": lambda x: x.strip() if x else None,
            },
            "planning_officer": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Planning Officer"]]/text()[2]',
                "transform": lambda x: x.strip() if x else None,
            },
            "recommendation": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Recommendation"]]/text()[2]',
                "transform": lambda x: x.strip() if x else None,
            },
            "determination_level": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Determination Level"]]/text()[2]',
                "transform": lambda x: x.strip() if x else None,
            },
            "existing_land_use": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Existing Land Use"]]/text()[2]',
                "transform": lambda x: x.strip() if x else None,
            },
            "proposed_land_use": {
                "xpath": '//div[@class="dataview"]//li/div[span[text()="Proposed Land Use"]]/text()[2]',
                "transform": lambda x: x.strip() if x else None,
            },
        }

        # Loop through each field mapping and extract the data
        for field, mapping in field_mappings.items():
            xpath = mapping["xpath"]
            transform = mapping.get("transform")

            value = response.xpath(xpath).get()
            if value:
                if transform:
                    try:
                        processed_value = transform(value)
                        setattr(planning_application, field, processed_value)
                    except Exception as e:
                        self.logger.error(f"Error processing {field}: {e}")
                else:
                    setattr(planning_application, field, value.strip())

        print("-" * 100)
        print(planning_application)
        print("-" * 100)

    def _transform_date(self, date_string):
        date_string = date_string.strip() if date_string else ""
        if not date_string:
            return None
        try:
            return datetime.strptime(date_string, "%d/%m/%Y")
        except Exception:
            return f"error parsing date: got {date_string}"

    def _extract_decision_status(self, text):
        if not text or text.strip() == "":
            return None

        parts = text.strip().split()
        if len(parts) < 2:
            return text.strip()

        # Return just the status part (excluding the date)
        return " ".join(parts[:-1])

    def _extract_decision_date(self, text):
        if not text or text.strip() == "":
            return None

        parts = text.strip().split()
        if len(parts) < 2:
            return None

        try:
            date_string = parts[-1]
            return datetime.strptime(date_string, "%d/%m/%Y")
        except Exception:
            return None

    def _transform_easting_northing(self, text):
        if not text or text.strip() == "":
            return None

        parts = text.strip().split()
        if len(parts) < 4:
            return text.strip()

        try:
            easting = float(parts[1])
            northing = float(parts[3])

            # Convert from EPSG:27700 (UK National Grid) to EPSG:4326 (WGS84)
            # Note: transformer.transform returns (longitude, latitude)
            lon, lat = self.transformer.transform(easting, northing)

            # Create a GeoJSON Point with WGS84 coordinates
            geojson = {
                "type": "Point",
                "coordinates": [lon, lat],  # GeoJSON uses [longitude, latitude] order
            }

            return json.dumps(geojson)
        except Exception as e:
            self.logger.error(f"Error converting coordinates to GeoJSON: {e}")
            return text.strip()


# def _parse_application_progress_summary(self, dataview) -> dict:

# def _parse_application_details(self, dataview) -> dict:

# def _parse_other_information(self, dataview) -> dict:

# to do: parse comments as well (separate page)
# TODO -- Grab the planning application documents (including comments) PDFs. Link is always https://planning2.wandsworth.gov.uk/planningcase/comments.aspx?case=$APPLICATION_NUMBER
#       -- The documents page runs on JS, so that's annoying. Can we reverse engineer the API?
#       -- For now, we'
