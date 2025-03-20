from typing import List

from planning_applications.spiders.northgate import NorthgateSpider


class WandsworthSpider(NorthgateSpider):
    name: str = "wandsworth"
    domain: str = "planning.wandsworth.gov.uk"
    allowed_domains: List[str] = [domain]
    start_url: str = f"https://{domain}/Northgate/PlanningExplorer/GeneralSearch.aspx"

    not_yet_working = True
