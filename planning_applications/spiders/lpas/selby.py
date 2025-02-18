from typing import List

from planning_applications.spiders.idox import IdoxSpider


class SelbySpider(IdoxSpider):
    name: str = "selby"
    domain: str = "public.selby.gov.uk"
    allowed_domains: List[str] = [domain]
    start_url: str = f"https://{domain}/online-applications"
    arcgis_url: str = f"https://{domain}/server/rest/services/PALIVE/LIVEUniformPA_Planning/FeatureServer/2/query"
