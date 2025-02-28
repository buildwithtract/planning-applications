from typing import Any

from planning_applications.db import (
    get_connection,
    get_cursor,
    upsert_planning_application,
    upsert_planning_application_appeal,
    upsert_planning_application_appeal_document,
    upsert_planning_application_document,
    upsert_planning_application_geometry,
)
from planning_applications.items import (
    IdoxPlanningApplicationGeometry,
    IdoxPlanningApplicationItem,
    PlanningApplicationAppeal,
    PlanningApplicationAppealDocument,
    PlanningApplicationItem,
)


class IdoxPlanningApplicationPipeline:
    def process_item(self, idox_item: IdoxPlanningApplicationItem | Any, spider) -> PlanningApplicationItem:
        if not isinstance(idox_item, IdoxPlanningApplicationItem):
            return idox_item

        spider.logger.info("Mapping item")

        item = PlanningApplicationItem(
            lpa=idox_item["lpa"],
            website_reference=idox_item["idox_key_val"],
            reference=idox_item["reference"],
            url=idox_item["url"],
            submitted_date=idox_item["application_received"],
            validated_date=idox_item["application_validated"],
            address=idox_item["address"],
            description=idox_item["proposal"],
            application_status=idox_item["status"],
            application_decision=idox_item["decision"],
            application_decision_date=idox_item["decision_issued_date"],
            appeal_status=idox_item["appeal_status"],
            appeal_decision=idox_item["appeal_decision"],
            appeal_decision_date=None,  # TODO: Add this
            application_type=idox_item["application_type"],
            expected_decision_level=idox_item["expected_decision_level"],
            actual_decision_level=idox_item["actual_decision_level"],
            case_officer=idox_item["case_officer"],
            parish=idox_item["parish"],
            ward=idox_item["ward"],
            amenity_society=idox_item["amenity_society"],
            district_reference=idox_item["district_reference"],
            applicant_name=idox_item["applicant_name"],
            applicant_address=idox_item["applicant_address"],
            environmental_assessment_requested=idox_item["environmental_assessment_requested"]
            if idox_item["environmental_assessment_requested"]
            else None,
            is_active=idox_item["is_active"],
            documents=idox_item["documents"],
            geometry=idox_item["geometry"],
        )

        return item


class PostgresPipeline:
    def __init__(self):
        self.connection = get_connection()
        self.cur = get_cursor(self.connection)

    def process_item(self, item: PlanningApplicationItem | PlanningApplicationAppeal, spider):
        if isinstance(item, PlanningApplicationAppealDocument):
            return self.process_appeal_case_document_item(item, spider)

        if isinstance(item, PlanningApplicationAppeal):
            return self.process_appeal_case_item(item, spider)

        if isinstance(item, PlanningApplicationItem):
            return self.process_planning_application_item(item, spider)

    def process_appeal_case_item(self, item: PlanningApplicationAppeal, spider):
        spider.logger.info(f"Inserting planning application appeal {item.reference}")
        try:
            _ = upsert_planning_application_appeal(self.cur, item)
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            spider.logger.error(f"Error inserting appeal case into the database: {e}")
            raise

    def process_appeal_case_document_item(self, item: PlanningApplicationAppealDocument, spider):
        spider.logger.info(f"Inserting planning application appeal document {item.reference}")
        try:
            _ = upsert_planning_application_appeal_document(self.cur, item)
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            spider.logger.error(f"Error inserting appeal case document into the database: {e}")
            raise

    def process_planning_application_item(self, item: PlanningApplicationItem, spider):
        spider.logger.info(f"Inserting planning application {item['reference']}")

        try:
            uuid = upsert_planning_application(self.cur, item)

            for document in item["documents"]:
                _ = upsert_planning_application_document(self.cur, uuid, document)

            geometry: IdoxPlanningApplicationGeometry = item["geometry"]
            _ = upsert_planning_application_geometry(self.cur, uuid, geometry)

            self.connection.commit()

        except Exception as e:
            self.connection.rollback()
            spider.logger.error(f"Error inserting item into the database: {e}")
            raise

        return item

    def close_spider(self, spider):
        self.cur.close()
        self.connection.close()
