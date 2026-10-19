"""Import a local catalog-v1 JSON batch; stdout is a sanitized JSON summary."""

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import NoReturn

from schemas.settings import Settings
from services.catalog_import import ImportReport, RowIssue, import_catalog


class CommandArgumentsError(Exception):
    """Do not echo unrecognized arguments or private path values."""


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise CommandArgumentsError from None


def main(argv: Sequence[str] | None = None) -> int:
    parser = Parser(prog="python -m scripts.import_catalog", description=__doc__)
    parser.add_argument(
        "batch", type=Path, help="Local UTF-8 catalog-v1 JSON file (maximum 5 MiB)."
    )
    parser.add_argument(
        "--database", type=Path, help="Existing initialized database; defaults to Settings."
    )
    parser.add_argument(
        "--update-resolutions",
        action="store_true",
        help="Explicitly replace differing stored resolutions after reviewing their evidence.",
    )
    try:
        arguments = parser.parse_args(argv)
        settings = Settings()
        report = import_catalog(
            arguments.batch,
            arguments.database or settings.database_path,
            update_resolutions=arguments.update_resolutions,
        )
    except CommandArgumentsError:
        report = ImportReport(
            status="failed",
            rows_known=False,
            issues=(
                RowIssue(
                    "command", "Supply a batch path and supported options. Use --help for syntax."
                ),
            ),
        )
    except (ValueError, OSError):
        report = ImportReport(
            status="failed",
            rows_known=False,
            issues=(
                RowIssue(
                    "configuration",
                    "Check readable configuration, supported ADVISOR_ settings "
                    "and non-empty paths.",
                ),
            ),
        )
    print(json.dumps(asdict(report), sort_keys=True))
    return 0 if report.status in ("committed", "unchanged") else 1


if __name__ == "__main__":
    raise SystemExit(main())
