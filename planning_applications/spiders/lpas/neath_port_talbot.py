from typing import List

from planning_applications.spiders.idox import IdoxSpider


class NeathPortTalbotSpider(IdoxSpider):
    name: str = "neath_port_talbot"
    domain: str = "planningonline.npt.gov.uk"
    allowed_domains: List[str] = [domain]
    start_url: str = f"https://{domain}/online-applications"
    arcgis_url: str = f"https://{domain}/server/rest/services/PALIVE/LIVEUniformPA_Planning/FeatureServer/2/query"
