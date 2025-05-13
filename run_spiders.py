import argparse
import os
from datetime import date, datetime
from typing import List, Optional, Tuple

from dateutil import relativedelta
from rich import print
from rich.console import Console
from rich.table import Table
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from planning_applications.db import get_earliest_date_for_lpa
from planning_applications.settings import DEFAULT_DATE_FORMAT


def get_spider_names(skip_not_working: bool = False) -> List[str]:
    spider_names = []
    spiders_dir = "planning_applications/spiders/lpas"

    # Skip __init__.py and get all .py files
    for file in os.listdir(spiders_dir):
        if file.endswith(".py") and file != "__init__.py":
            spider_name = file[:-3]  # Remove .py extension
            if skip_not_working:
                module = __import__(f"planning_applications.spiders.lpas.{spider_name}", fromlist=["*"])
                spider_class = next(
                    (
                        cls
                        for name, cls in module.__dict__.items()
                        if isinstance(cls, type)
                        and name.endswith("Spider")
                        and getattr(cls, "name", None) == spider_name
                    ),
                    None,
                )
                if spider_class and getattr(spider_class, "not_yet_working", False):
                    print(f"[green]Skipping spider {spider_name} because it is not yet working[/green]")
                    continue
            spider_names.append(spider_name)

    return sorted(spider_names)


def parse_date(date_str: str) -> date:
    return datetime.strptime(date_str, DEFAULT_DATE_FORMAT).date()


def parse_lpa_dates(lpa_dates: List[str]) -> List[Tuple[str, date, date]]:
    """Parse list of lpa,start_date,end_date strings."""
    result = []
    today = date.today()

    for lpa_date in lpa_dates:
        try:
            lpa, start, end = lpa_date.split(",")
            start_date = parse_date(start)
            end_date = parse_date(end)

            if start_date > end_date:
                print(f"[yellow]Start date {start_date} is in the future for LPA {lpa}, adjusting to {today}[/yellow]")
                start_date = today

            if start_date > date.today():
                print(f"[yellow]Start date {start_date} is in the future for LPA {lpa}[/yellow]")
                continue

            result.append((lpa, start_date, end_date))
        except ValueError as e:
            raise ValueError(f"Invalid lpa,start_date,end_date format: {lpa_date}. Error: {e}")
    return result


def get_spider_info(
    name: str, from_earliest: bool = False, lpa_dates: Optional[List[Tuple[str, date, date]]] = None
) -> Tuple[str, str, str | None, str, str] | None:
    earliest_date = None
    start = None
    end = None

    if lpa_dates:
        mode = "LPA Dates"
        lpa_config = next((x for x in lpa_dates if x[0] == name), None)
        if lpa_config:
            start, end = lpa_config[1], lpa_config[2]
        else:
            print(f"[yellow]No LPA date config found for {name}. Skipping spider.[/yellow]")
            return None

    elif from_earliest:
        mode = "From Earliest"
        earliest_date = get_earliest_date_for_lpa(name)
        if earliest_date:
            start = min(
                earliest_date + relativedelta.relativedelta(months=1),
                date.today() - relativedelta.relativedelta(weeks=1),
            )
            end = start + relativedelta.relativedelta(weeks=1)
        else:
            start = date.today() - relativedelta.relativedelta(weeks=1)
            end = date.today()
    else:
        print(f"[yellow]No option passed. Skipping spider {name}[/yellow]")
        return None

    earliest_date_str = earliest_date.strftime(DEFAULT_DATE_FORMAT) if earliest_date else None
    start_str = start.strftime(DEFAULT_DATE_FORMAT) if start else None
    end_str = end.strftime(DEFAULT_DATE_FORMAT) if end else None

    if not start_str or not end_str:
        print(f"[yellow]No start and/or end date found for {name}. Skipping spider.[/yellow]")
        return None

    return name, mode, earliest_date_str, start_str, end_str


def run_spiders(
    spider_names: List[str], from_earliest: bool = False, lpa_dates: Optional[List[Tuple[str, date, date]]] = None
) -> None:
    """Run multiple spiders using CrawlerProcess."""
    settings = get_project_settings()
    process = CrawlerProcess(settings)

    spider_info = []
    for spider_name in spider_names:
        row = get_spider_info(spider_name, from_earliest, lpa_dates)
        if row:
            spider_info.append(row)

    table = Table(title="Spider Dates Summary")
    table.add_column("Spider", style="cyan")
    table.add_column("Mode", style="magenta", justify="center")
    table.add_column("Earliest Date on Record", style="green", justify="center")
    table.add_column("Start Date", justify="center")
    table.add_column("End Date", justify="center")
    for name, mode, earliest_date, start, end in spider_info:
        table.add_row(name, mode, earliest_date, start, end)
    console = Console()
    console.print(table)

    for spider_name, mode, earliest_date, start, end in spider_info:
        spider_kwargs = {}
        spider_kwargs["start_date"], spider_kwargs["end_date"] = start, end
        process.crawl(spider_name, **spider_kwargs)
    process.start()


def run_appeals(
    from_date: date,
    to_date: date,
    metadata_only: bool = False,
) -> None:
    """Run the planning appeals spider with the given dates."""
    settings = get_project_settings()
    settings["DOWNLOAD_FILES"] = not metadata_only
    process = CrawlerProcess(settings)
    process.crawl("appeals", start_date=from_date, end_date=to_date)
    process.start()


def main():
    parser = argparse.ArgumentParser(description="Run planning application spiders")
    subparsers = parser.add_subparsers(help="sub-command help", dest="command")

    appeals_parser = subparsers.add_parser(
        "appeals",
        description="Planning appeals spider",
    )
    appeals_parser.add_argument(
        "--from-date",
        type=date.fromisoformat,
        required=True,
        help="Start date, inclusive (YYYY-MM-DD)",
    )
    appeals_parser.add_argument(
        "--to-date",
        type=date.fromisoformat,
        required=True,
        help="End date, inclusive (YYYY-MM-DD)",
    )
    appeals_parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="Do not download files to S3, just scrape the metadata",
    )

    lpas_parser = subparsers.add_parser(
        "lpas",
        description="Planning applications for local authorities",
    )

    group = lpas_parser.add_mutually_exclusive_group()
    group.add_argument(
        "--all",
        action="store_true",
        help="Run all working spiders with default dates",
    )

    lpas_parser.add_argument(
        "--from-earliest",
        action="store_true",
        help="Start from earliest date in database plus one month for all spiders",
    )
    lpas_parser.add_argument(
        "--lpa-dates",
        nargs="+",
        help="List of LPA,start_date,end_date (e.g., 'cambridge,2024-01-01,2024-02-01')",
    )
    lpas_parser.add_argument(
        "--lpas-from-earliest",
        nargs="+",
        help="List of LPA names to run from their earliest dates (e.g., 'cambridge barnet')",
    )
    args = parser.parse_args()

    if args.command == "appeals":
        appeals_args = vars(args)
        del appeals_args["command"]
        run_appeals(
            from_date=appeals_args["from_date"],
            to_date=appeals_args["to_date"],
            metadata_only=appeals_args.get("metadata_only", False),
        )
        return

    if args.command == "lpas":
        all_spider_names = get_spider_names(skip_not_working=args.all)

        if args.lpas_from_earliest:
            invalid_lpas = [lpa for lpa in args.lpas_from_earliest if lpa not in all_spider_names]
            if invalid_lpas:
                print(f"[red]Error: Invalid LPA names: {', '.join(invalid_lpas)}[/red]")
                return
            run_spiders(args.lpas_from_earliest, from_earliest=True)
        elif args.lpa_dates:
            lpa_dates = parse_lpa_dates(args.lpa_dates)
            run_spiders(all_spider_names, lpa_dates=lpa_dates)
        else:
            run_spiders(all_spider_names, from_earliest=args.from_earliest)
        return

    raise ValueError(f"Invalid command {args.command}")


if __name__ == "__main__":
    main()
