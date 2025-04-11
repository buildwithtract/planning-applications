import json

import psycopg

from planning_applications.utils import getenv, to_datetime_or_none

database_url = getenv("DATABASE_URL")


def get_connection():
    return psycopg.connect(database_url)


def get_cursor(connection):
    return connection.cursor()


def upsert_scraper_run(cursor: psycopg.Cursor, name: str, stats: dict):
    cursor.execute(
        """ INSERT INTO scraper_runs (
                name,
                last_finished_at,
                last_data_found_at,
                last_run_stats
            ) VALUES (%s,%s,%s,%s)
            ON CONFLICT (name)
            DO UPDATE SET
                last_finished_at = EXCLUDED.last_finished_at,
                last_data_found_at = COALESCE(EXCLUDED.last_data_found_at, scraper_runs.last_data_found_at),
                last_run_stats = EXCLUDED.last_run_stats
            """,
        (
            name,
            to_datetime_or_none(stats.get("finish_time")),
            to_datetime_or_none(stats.get("finish_time")) if stats.get("item_scraped_count", 0) > 0 else None,
            json.dumps(stats, default=str),
        ),
    )

    row = cursor.rowcount
    if row != 1:
        raise ValueError(f"Expected 1 row to be updated, but got {row}")
