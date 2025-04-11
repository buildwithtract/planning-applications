from datetime import date
from typing import Optional

import psycopg

from planning_applications.items import (
    IdoxPlanningApplicationGeometry,
    PlanningApplication,
    PlanningApplicationAppeal,
    PlanningApplicationAppealDocument,
    PlanningApplicationDocument,
    PlanningApplicationGeometry,
)
from planning_applications.settings import DEFAULT_DATE_FORMAT
from planning_applications.utils import to_datetime_or_none
from shared.db import get_connection, get_cursor

# Selects
# -------------------------------------------------------------------------------------------------


def select_planning_application_by_url(url: str) -> Optional[PlanningApplication]:
    cursor = get_cursor(get_connection())

    cursor.execute("SELECT * FROM planning_applications WHERE URL = %s", (url,))
    row = cursor.fetchone()
    if not row:
        return None

    lpa = row[1]
    reference = row[2]
    website_reference = row[3]
    url = row[4]
    submitted_date = row[5]
    validated_date = row[6]
    address = row[7]
    description = row[8]
    application_status = row[9]
    application_decision = row[10]
    application_decision_date = to_datetime_or_none(row[11])
    appeal_status = row[12]
    appeal_decision = row[13]
    appeal_decision_date = to_datetime_or_none(row[14])
    application_type = row[15]
    expected_decision_level = row[16]
    actual_decision_level = row[17]
    case_officer = row[18]
    parish = row[19]
    ward = row[20]
    amenity_society = row[21]
    district_reference = row[22]
    applicant_name = row[23]
    applicant_address = row[24]
    environmental_assessment_requested = row[25]
    is_active = row[26]

    cursor.close()

    return PlanningApplication(
        lpa=lpa,
        reference=reference,
        website_reference=website_reference,
        url=url,
        submitted_date=submitted_date,
        validated_date=validated_date,
        address=address,
        description=description,
        application_status=application_status,
        application_decision=application_decision,
        application_decision_date=application_decision_date,
        appeal_status=appeal_status,
        appeal_decision=appeal_decision,
        appeal_decision_date=appeal_decision_date,
        application_type=application_type,
        expected_decision_level=expected_decision_level,
        actual_decision_level=actual_decision_level,
        case_officer=case_officer,
        parish=parish,
        ward=ward,
        amenity_society=amenity_society,
        district_reference=district_reference,
        applicant_name=applicant_name,
        applicant_address=applicant_address,
        environmental_assessment_requested=environmental_assessment_requested,
        is_active=is_active,
    )


def get_planning_application_uuid_for_lpa_and_reference(
    cursor: psycopg.Cursor, lpa: str, reference: str
) -> str | None:
    cursor.execute(
        """
        SELECT uuid FROM planning_applications WHERE lpa = %s AND reference = %s
        """,
        (lpa, reference),
    )
    row = cursor.fetchone()
    if not row:
        return None
    return row[0]


def get_earliest_date_for_lpa(lpa: str) -> Optional[date]:
    """Get the earliest validated_date for an LPA from the database."""
    conn = get_connection()

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT validated_date FROM planning_applications WHERE lpa = %s ORDER BY validated_date ASC LIMIT 1
            """,
            (lpa,),
        )
        result = cur.fetchone()

    conn.close()

    if result and result[0]:
        # Return the first day of the month after the earliest date
        earliest_date = result[0]
        if earliest_date.month == 12:
            return date(earliest_date.year + 1, 1, 1)
        return date(earliest_date.year, earliest_date.month + 1, 1)

    # If no records found, return None to use default date
    return None


# Upserts
# -------------------------------------------------------------------------------------------------


def upsert_planning_application(cursor: psycopg.Cursor, item: PlanningApplication) -> str:
    cursor.execute(
        """ INSERT INTO planning_applications (
                lpa,
                reference,
                website_reference,
                url,
                submitted_date,
                validated_date,
                address,
                description,
                application_status,
                application_decision,
                application_decision_date,
                appeal_status,
                appeal_decision,
                appeal_decision_date,
                application_type,
                expected_decision_level,
                actual_decision_level,
                case_officer,
                case_officer_phone,
                parish,
                ward,
                amenity_society,
                comments_due_date,
                committee_date,
                district_reference,
                applicant_name,
                applicant_address,
                agent_name,
                agent_address,
                environmental_assessment_requested,
                is_active
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (lpa, reference)
            DO UPDATE SET
                website_reference = EXCLUDED.website_reference,
                url = EXCLUDED.url,
                submitted_date = EXCLUDED.submitted_date,
                validated_date = EXCLUDED.validated_date,
                address = EXCLUDED.address,
                description = EXCLUDED.description,
                application_status = EXCLUDED.application_status,
                application_decision = EXCLUDED.application_decision,
                application_decision_date = EXCLUDED.application_decision_date,
                appeal_status = EXCLUDED.appeal_status,
                appeal_decision = EXCLUDED.appeal_decision,
                appeal_decision_date = EXCLUDED.appeal_decision_date,
                application_type = EXCLUDED.application_type,
                expected_decision_level = EXCLUDED.expected_decision_level,
                actual_decision_level = EXCLUDED.actual_decision_level,
                case_officer = EXCLUDED.case_officer,
                case_officer_phone = EXCLUDED.case_officer_phone,
                parish = EXCLUDED.parish,
                ward = EXCLUDED.ward,
                amenity_society = EXCLUDED.amenity_society,
                comments_due_date = EXCLUDED.comments_due_date,
                committee_date = EXCLUDED.committee_date,
                district_reference = EXCLUDED.district_reference,
                applicant_name = EXCLUDED.applicant_name,
                applicant_address = EXCLUDED.applicant_address,
                agent_name = EXCLUDED.agent_name,
                agent_address = EXCLUDED.agent_address,
                environmental_assessment_requested = EXCLUDED.environmental_assessment_requested,
                is_active = EXCLUDED.is_active,
                last_imported_at = NOW()
            RETURNING uuid;
            """,
        (
            item.lpa,
            item.reference,
            item.website_reference,
            item.url,
            item.submitted_date,
            item.validated_date,
            item.address,
            item.description,
            item.application_status,
            item.application_decision,
            item.application_decision_date,
            item.appeal_status,
            item.appeal_decision,
            item.appeal_decision_date,
            item.application_type,
            item.expected_decision_level,
            item.actual_decision_level,
            item.case_officer,
            item.case_officer_phone,
            item.parish,
            item.ward,
            item.amenity_society,
            item.comments_due_date,
            item.committee_date,
            item.district_reference,
            item.applicant_name,
            item.applicant_address,
            item.agent_name,
            item.agent_address,
            item.environmental_assessment_requested,
            item.is_active,
        ),
    )

    row = cursor.fetchone()
    if not row:
        raise ValueError("No row returned from the upsert query!")
    return row[0]


def upsert_planning_application_item(cursor: psycopg.Cursor, item: PlanningApplication) -> str:
    cursor.execute(
        """ INSERT INTO planning_applications (
                lpa,
                reference,
                website_reference,
                url,
                submitted_date,
                validated_date,
                address,
                description,
                application_status,
                application_decision,
                application_decision_date,
                appeal_status,
                appeal_decision,
                appeal_decision_date,
                application_type,
                expected_decision_level,
                actual_decision_level,
                case_officer,
                parish,
                ward,
                amenity_society,
                district_reference,
                applicant_name,
                applicant_address,
                environmental_assessment_requested,
                is_active
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (lpa, reference)
            DO UPDATE SET
                website_reference = EXCLUDED.website_reference,
                url = EXCLUDED.url,
                submitted_date = EXCLUDED.submitted_date,
                validated_date = EXCLUDED.validated_date,
                address = EXCLUDED.address,
                description = EXCLUDED.description,
                application_status = EXCLUDED.application_status,
                application_decision = EXCLUDED.application_decision,
                application_decision_date = EXCLUDED.application_decision_date,
                appeal_status = EXCLUDED.appeal_status,
                appeal_decision = EXCLUDED.appeal_decision,
                appeal_decision_date = EXCLUDED.appeal_decision_date,
                application_type = EXCLUDED.application_type,
                expected_decision_level = EXCLUDED.expected_decision_level,
                actual_decision_level = EXCLUDED.actual_decision_level,
                case_officer = EXCLUDED.case_officer,
                parish = EXCLUDED.parish,
                ward = EXCLUDED.ward,
                amenity_society = EXCLUDED.amenity_society,
                district_reference = EXCLUDED.district_reference,
                applicant_name = EXCLUDED.applicant_name,
                applicant_address = EXCLUDED.applicant_address,
                environmental_assessment_requested = EXCLUDED.environmental_assessment_requested,
                is_active = EXCLUDED.is_active,
                last_imported_at = NOW()
            RETURNING uuid;
            """,
        (
            item.lpa,
            item.reference,
            item.website_reference,
            item.url,
            item.submitted_date,
            item.validated_date,
            item.address,
            item.description,
            item.application_status,
            item.application_decision,
            item.application_decision_date,
            item.appeal_status,
            item.appeal_decision,
            item.appeal_decision_date,
            item.application_type,
            item.expected_decision_level,
            item.actual_decision_level,
            item.case_officer,
            item.parish,
            item.ward,
            item.amenity_society,
            item.district_reference,
            item.applicant_name,
            item.applicant_address,
            item.environmental_assessment_requested,
            item.is_active,
        ),
    )

    row = cursor.fetchone()
    if not row:
        raise ValueError("No row returned from the upsert query!")
    return row[0]


def upsert_planning_application_document(
    cursor: psycopg.Cursor, planning_application_uuid: str, document: PlanningApplicationDocument
) -> str:
    cursor.execute(
        """ INSERT INTO planning_application_documents (
                planning_application_uuid,
                date_published,
                document_type,
                description,
                url,
                drawing_number
            ) VALUES (%s,%s,%s,%s,%s,%s)
            ON CONFLICT (url)
            DO UPDATE SET
                date_published = EXCLUDED.date_published,
                document_type = EXCLUDED.document_type,
                description = EXCLUDED.description,
                drawing_number = EXCLUDED.drawing_number,
                last_imported_at = NOW()
            RETURNING uuid;
            """,
        (
            planning_application_uuid,
            document.date_published,
            document.document_type,
            document.description,
            document.url,
            document.drawing_number,
        ),
    )

    row = cursor.fetchone()
    if not row:
        raise ValueError("No row returned from the upsert query!")
    return row[0]


def upsert_planning_application_geometry(
    cursor: psycopg.Cursor,
    planning_application_uuid: str,
    geometry: PlanningApplicationGeometry | IdoxPlanningApplicationGeometry,
) -> str:
    cursor.execute(
        """ INSERT INTO planning_application_geometries (
                planning_application_uuid,
                reference,
                geometry
            ) VALUES (%s,%s,%s)
            ON CONFLICT (planning_application_uuid, reference)
            DO UPDATE SET
                geometry = EXCLUDED.geometry,
                last_imported_at = NOW()
            RETURNING uuid;
""",
        (planning_application_uuid, geometry.reference, geometry.geometry),
    )

    row = cursor.fetchone()
    if not row:
        raise ValueError("No row returned from the upsert query!")
    return row[0]


def upsert_planning_application_appeal(cursor: psycopg.Cursor, item: PlanningApplicationAppeal) -> str:
    cursor.execute(
        """
        INSERT INTO planning_application_appeals (
            lpa,
            reference,
            case_id,
            url,
            appellant_name,
            agent_name,
            site_address,
            case_type,
            case_officer,
            procedure,
            status,
            decision,
            start_date,
            questionnaire_due_date,
            statement_due_date,
            interested_party_comments_due_date,
            final_comments_due_date,
            inquiry_evidence_due_date,
            event_date,
            decision_date,
            linked_case_ids,
            first_imported_at,
            last_imported_at
        )
        VALUES (
            %(lpa)s,
            %(reference)s,
            %(case_id)s,
            %(url)s,
            %(appellant_name)s,
            %(agent_name)s,
            %(site_address)s,
            %(case_type)s,
            %(case_officer)s,
            %(procedure)s,
            %(status)s,
            %(decision)s,
            %(start_date)s,
            %(questionnaire_due_date)s,
            %(statement_due_date)s,
            %(interested_party_comments_due_date)s,
            %(final_comments_due_date)s,
            %(inquiry_evidence_due_date)s,
            %(event_date)s,
            %(decision_date)s,
            %(linked_case_ids)s,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (case_id) DO UPDATE SET
            reference = EXCLUDED.reference,
            url = EXCLUDED.url,
            appellant_name = EXCLUDED.appellant_name,
            agent_name = EXCLUDED.agent_name,
            site_address = EXCLUDED.site_address,
            case_type = EXCLUDED.case_type,
            case_officer = EXCLUDED.case_officer,
            procedure = EXCLUDED.procedure,
            status = EXCLUDED.status,
            decision = EXCLUDED.decision,
            start_date = EXCLUDED.start_date,
            questionnaire_due_date = EXCLUDED.questionnaire_due_date,
            statement_due_date = EXCLUDED.statement_due_date,
            interested_party_comments_due_date = EXCLUDED.interested_party_comments_due_date,
            final_comments_due_date = EXCLUDED.final_comments_due_date,
            inquiry_evidence_due_date = EXCLUDED.inquiry_evidence_due_date,
            event_date = EXCLUDED.event_date,
            decision_date = EXCLUDED.decision_date,
            linked_case_ids = EXCLUDED.linked_case_ids,
            last_imported_at = CURRENT_TIMESTAMP
        RETURNING uuid;
        """,
        {
            "lpa": item.lpa,
            "reference": item.reference,
            "case_id": item.case_id,
            "url": item.url,
            "appellant_name": item.appellant_name,
            "agent_name": item.agent_name,
            "site_address": item.site_address,
            "case_type": item.case_type,
            "case_officer": item.case_officer,
            "procedure": item.procedure,
            "status": item.status,
            "decision": item.decision,
            "start_date": item.start_date,
            "questionnaire_due_date": item.questionnaire_due_date,
            "statement_due_date": item.statement_due_date,
            "interested_party_comments_due_date": item.interested_party_comments_due_date,
            "final_comments_due_date": item.final_comments_due_date,
            "inquiry_evidence_due_date": item.inquiry_evidence_due_date,
            "event_date": item.event_date,
            "decision_date": item.decision_date,
            "linked_case_ids": item.linked_case_ids,
        },
    )

    row = cursor.fetchone()
    if not row:
        raise ValueError("No row returned from the upsert query!")
    return row[0]


def upsert_planning_application_appeal_document(
    cursor: psycopg.Cursor, item: PlanningApplicationAppealDocument
) -> str:
    cursor.execute(
        """
        INSERT INTO planning_application_appeals_documents (
            planning_application_appeal_uuid,
            appeal_case_id,
            reference,
            name,
            url,
            s3_path
        )
        VALUES (
            (SELECT uuid FROM planning_application_appeals WHERE case_id = %(appeal_case_id)s),
            %(appeal_case_id)s,
            %(reference)s,
            %(name)s,
            %(url)s,
            %(s3_path)s
        )
        ON CONFLICT (url) DO UPDATE SET
            name = EXCLUDED.name,
            last_imported_at = NOW()
        RETURNING uuid;
        """,
        {
            "appeal_case_id": item.appeal_case_id,
            "reference": item.reference,
            "name": item.name,
            "url": item.url,
            "s3_path": item.s3_path,
        },
    )

    row = cursor.fetchone()
    if not row:
        raise ValueError("No row returned from the upsert query!")
    return row[0]
