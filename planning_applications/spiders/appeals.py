import os
import re
from datetime import date, datetime
from re import I

import parsel
import parsel.selector
import scrapy
from scrapy.http.response import Response
from scrapy.http.response.text import TextResponse

from planning_applications.items import PlanningApplicationAppeal, PlanningApplicationAppealDocument
from planning_applications.settings import DEFAULT_DATE_FORMAT

DEFAULT_START_DATE = datetime(datetime.now().year, datetime.now().month, 1).date()
DEFAULT_END_DATE = datetime.now().date()

EARLIEST_KNOWN_CASE_ID = int(os.getenv("APPEALS_SPIDER_EARLIEST_KNOWN_CASE_ID", 2005083))


class AppealsSpider(scrapy.Spider):
    name = "appeals"
    base_url = "https://acp.planninginspectorate.gov.uk"
    allowed_domains = ["acp.planninginspectorate.gov.uk"]
    start_url = f"{base_url}/CaseSearch.aspx"

    start_date: date | None = None
    end_date: date | None = None
    from_case_id: int | None = None
    to_case_id: int | None = None

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        if isinstance(self.from_case_id, str):
            self.from_case_id = int(self.from_case_id)

        if isinstance(self.to_case_id, str):
            self.to_case_id = int(self.to_case_id)

        if self.from_case_id and not self.to_case_id or self.to_case_id and not self.from_case_id:
            raise ValueError("to_case_id and from_case_id must be provided together")

        if self.from_case_id and self.to_case_id:
            if self.from_case_id > self.to_case_id:
                raise ValueError(f"from_case_id {self.from_case_id} must be less than to_case_id {self.to_case_id}")

            if self.start_date or self.end_date:
                raise ValueError("start_date and end_date must not be provided when from_case_id is provided")

            return

        if isinstance(self.start_date, str):
            self.start_date = datetime.strptime(self.start_date, DEFAULT_DATE_FORMAT).date()

        if isinstance(self.end_date, str):
            self.end_date = datetime.strptime(self.end_date, DEFAULT_DATE_FORMAT).date()

        if not self.start_date or not self.end_date:
            raise ValueError("start_date and end_date must be provided when from_case_id is not provided")

        if self.start_date > self.end_date:
            raise ValueError(f"start_date {self.start_date} must not be later than end_date {self.end_date}")

        if self.start_date > datetime.now().date():
            raise ValueError(f"start_date {self.start_date} must be in the past")

    def start_requests(self):
        """
        First entry point: load the advanced search page so we can get the form/CSRF token.
        """

        if self.from_case_id and self.to_case_id:
            self.logger.info(
                f"Searching for appeals received between case IDs {self.from_case_id} and {self.to_case_id} inclusively"
            )
            yield from self.issue_requests_for_case_ids()
            return

        self.logger.info(f"Searching for appeals received between {self.start_date} and {self.end_date}")

        yield scrapy.Request(self.start_url, callback=self.get_case_ids_for_date_range, meta={"dont_redirect": True})

    def issue_requests_for_case_ids(self):
        self.logger.info(f"Issuing requests for case IDs between {self.from_case_id} and {self.to_case_id}")

        for case_id in range(self.from_case_id or EARLIEST_KNOWN_CASE_ID, self.to_case_id or 0):
            yield scrapy.Request(
                url=f"{self.base_url}/ViewCase.aspx?CaseID={case_id}&CoID=0",
                callback=self.parse_case,
                meta={"dont_redirect": True},
            )

    def parse_case(self, response: Response):
        case_id = int(response.url.split("CaseID=")[1].split("&")[0])
        if "No case found with Case ID" in response.text:
            self.logger.warn(f"No case found with Case ID {case_id}. Skipping.")
            return

        self.logger.info(f"Found case ID {case_id}. Parsing.")

        reference = (
            (response.css("h2#cphMainContent_LabelCaseReference::text").get() or "").replace("Reference: ", "").strip()
        )
        if not reference:
            self.logger.warn(f"No reference found for case ID {case_id}. Skipping.")
            return

        lpa = response.css("#cphMainContent_labLPAName::text").get()
        if not lpa:
            self.logger.warn(f"No local planning authority found for case ID {case_id}. Skipping.")
            return

        item_data = {
            "lpa": lpa,
            "url": response.url,
            "reference": reference,
            "case_id": case_id,
            "appellant_name": response.css("#cphMainContent_labName::text").get() or None,
            "agent_name": response.css("#cphMainContent_labAgentName::text").get() or None,
            "site_address": response.css("#cphMainContent_labSiteAddress::text").get() or None,
            "case_type": response.css("#cphMainContent_labCaseTypeName::text").get() or None,
            "case_officer": response.css("#cphMainContent_labCaseOfficer::text").get() or None,
            "procedure": response.css("#cphMainContent_labProcedure::text").get() or None,
            "status": response.css("#cphMainContent_labStatus::text").get() or None,
            "decision": response.css("#cphMainContent_labOutcome::text").get() or None,
            "start_date": response.css("#cphMainContent_labStartDate::text").get() or None,
            "questionnaire_due_date": response.css("#cphMainContent_labQuestionnaireDueDate::text").get() or None,
            "statement_due_date": response.css("#cphMainContent_labAppellantLPARepsDueDate::text").get() or None,
            "interested_party_comments_due_date": response.css(
                "#cphMainContent_labInterestedPartyCommentsDueDate::text"
            ).get()
            or None,
            "final_comments_due_date": response.css("#cphMainContent_labFinalCommentsDueDate::text").get() or None,
            "inquiry_evidence_due_date": response.css("#cphMainContent_labInquiryEvidenceDueDate::text").get() or None,
            "event_date": response.css("#cphMainContent_labEventDate::text").get() or None,
            "decision_date": response.css("#cphMainContent_labDecisionDate::text").get() or None,
        }

        linked_case_ids = []
        for case_anchor in response.css('a[id^="cphMainContent_repLinkedCases_lnkLinkedCase_"]'):
            linked_case_id = self._parse_case_id_from_anchor(case_anchor)
            if linked_case_id:
                linked_case_ids.append(linked_case_id)
        item_data["linked_case_ids"] = linked_case_ids

        for date_key in [
            "start_date",
            "questionnaire_due_date",
            "statement_due_date",
            "interested_party_comments_due_date",
            "final_comments_due_date",
            "inquiry_evidence_due_date",
            "event_date",
            "decision_date",
        ]:
            try:
                item_data[date_key] = datetime.strptime(item_data[date_key], DEFAULT_DATE_FORMAT).date()
            except ValueError:
                item_data[date_key] = None

        self.logger.info(f"Yielding item for case ID {case_id}")
        yield PlanningApplicationAppeal(**item_data)

        # Does this case have any documents?
        documents_container = response.css("#cphMainContent_labDecisionLink")
        if documents_container:
            self.logger.info(f"Found documents for case ID {case_id}")

            for documents_anchor in documents_container.css("a"):
                if documents_anchor:
                    document_path = documents_anchor.css("::attr(href)").get()
                    if not document_path:
                        self.logger.error(f"No document path found for case ID {case_id}. This should never happen.")
                        continue

                    document_url = f"{self.base_url}/{document_path}"
                    document_id = document_path.split("fileid=")[1].split("&")[0]
                    document_name = documents_anchor.css("::text").get()

                    yield PlanningApplicationAppealDocument(
                        appeal_case_id=case_id,
                        reference=document_id,
                        name=document_name or document_url,
                        url=document_url,
                    )

    def _parse_case_id_from_anchor(self, case_anchor: parsel.selector.Selector):
        case_url = case_anchor.css("::attr(href)").get()
        if not case_url:
            return None

        case_id = re.search(r"caseid=(\d+)", case_url, re.IGNORECASE)
        if not case_id:
            return None

        return int(case_id.group(1))

    def get_case_ids_for_date_range(self, response: Response):
        """
        The appeals registry gives us a monotonically increasing case ID, which allows us to loop
        through cases within our date range nice and quickly.

        But to do that we need to know the lowest and highest case IDs within our date range.
        """
        if not isinstance(response, TextResponse):
            self.logger.error("get_case_ids_for_date_range must be called with a TextResponse")
            return
        yield from self._find_highest_case_id(response, self.end_date or datetime.now().date())

    def _find_highest_case_id(self, response: TextResponse, date: date):
        yield scrapy.FormRequest.from_response(
            response,
            formdata={
                "ctl00$hidIsListed": "No",
                "ctl00$cphMainContent$txtCaseReference": "",
                "ctl00$cphMainContent$txtStreet": "",
                "ctl00$cphMainContent$txtTownCity": "",
                "ctl00$cphMainContent$txtCounty": "",
                "ctl00$cphMainContent$txtPostCode": "",
                "ctl00$cphMainContent$txtSearchLPA": "",
                "ctl00$cphMainContent$txt_lparefnumber": "",
                "ctl00$cphMainContent$cboAppealType": "-1",
                "ctl00$cphMainContent$ppsAppellant$txtPerson": "",
                "ctl00$cphMainContent$ppsOtherParty$txtPerson": "",
                "ctl00$cphMainContent$pdsHearing$txtDateSearch": "",
                "ctl00$cphMainContent$pdsSiteVisit$txtDateSearch": "",
                "ctl00$cphMainContent$pdsCallIn$txtDateSearch": "",
                "ctl00$cphMainContent$pdsReceived$txtDateSearch": date.strftime("%d/%m/%Y"),
                "ctl00$cphMainContent$pdsDecision$txtDateSearch": "",
                "ctl00$cphMainContent$cboProcedureType": "-1",
                "ctl00$cphMainContent$cboStatus": "-1",
                "ctl00$cphMainContent$cmdSearch": "Search",
                "ctl00$cphMainContent$cboSearchLPA": "-1",
            },
            callback=self._parse_highest_case_id_from_search_results,
            dont_filter=True,
            meta={"dont_redirect": True, "original_response": response},
        )

    def _parse_highest_case_id_from_search_results(self, response: TextResponse):
        self.logger.info("Parsing search results to find highest case ID")

        highest_case_id = EARLIEST_KNOWN_CASE_ID
        for case_anchor in response.css('a[id^="cphMainContent_grdCaseResults_lnkViewCase_"]').getall():
            case_id = int(case_anchor.split("CaseID=")[1].split("&")[0])
            if case_id > highest_case_id:
                highest_case_id = case_id

        self.logger.info(f"Found highest case ID: {highest_case_id}")
        self.to_case_id = highest_case_id

        yield from self._find_lowest_case_id(
            response.meta["original_response"], self.start_date or datetime.now().date()
        )

    def _find_lowest_case_id(self, response: TextResponse, date: date):
        yield scrapy.FormRequest.from_response(
            response,
            formdata={
                "ctl00$hidIsListed": "No",
                "ctl00$cphMainContent$txtCaseReference": "",
                "ctl00$cphMainContent$txtStreet": "",
                "ctl00$cphMainContent$txtTownCity": "",
                "ctl00$cphMainContent$txtCounty": "",
                "ctl00$cphMainContent$txtPostCode": "",
                "ctl00$cphMainContent$txtSearchLPA": "",
                "ctl00$cphMainContent$txt_lparefnumber": "",
                "ctl00$cphMainContent$cboAppealType": "-1",
                "ctl00$cphMainContent$ppsAppellant$txtPerson": "",
                "ctl00$cphMainContent$ppsOtherParty$txtPerson": "",
                "ctl00$cphMainContent$pdsHearing$txtDateSearch": "",
                "ctl00$cphMainContent$pdsSiteVisit$txtDateSearch": "",
                "ctl00$cphMainContent$pdsCallIn$txtDateSearch": "",
                "ctl00$cphMainContent$pdsReceived$txtDateSearch": date.strftime("%d/%m/%Y"),
                "ctl00$cphMainContent$pdsDecision$txtDateSearch": "",
                "ctl00$cphMainContent$cboProcedureType": "-1",
                "ctl00$cphMainContent$cboStatus": "-1",
                "ctl00$cphMainContent$cmdSearch": "Search",
                "ctl00$cphMainContent$cboSearchLPA": "-1",
            },
            callback=self._parse_lowest_case_id_from_search_results,
            dont_filter=True,
            meta={"dont_redirect": True},
        )

    def _parse_lowest_case_id_from_search_results(self, response: TextResponse):
        self.logger.info("Parsing search results to find lowest case ID")

        lowest_case_id = self.to_case_id or EARLIEST_KNOWN_CASE_ID
        for case_anchor in response.css('a[id^="cphMainContent_grdCaseResults_lnkViewCase_"]').getall():
            case_id = int(case_anchor.split("CaseID=")[1].split("&")[0])
            if case_id < lowest_case_id:
                lowest_case_id = case_id

        if "Your search exceeded 250 results" in response.text:
            raise ValueError(f"""There are more than 250 cases for the date {self.start_date}.
                             
Due to an implementation detail, we don't currently support start_date searches for days which have more than 250 cases.
Please adjust the start date to be earlier and discard the oldest cases.""")

        self.logger.info(f"Found lowest case ID: {lowest_case_id}")
        self.from_case_id = lowest_case_id

        yield from self.issue_requests_for_case_ids()
