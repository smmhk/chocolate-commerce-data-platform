"""Export a PostgreSQL snapshot of raw_square.locations to UTF-8 CSV."""

import argparse
import csv
import logging
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from sqlalchemy import text

from src.load.postgres.connection import get_postgres_engine
from src.pipelines.run_logging import log_stage, run_cli, run_metadata

LOGGER = logging.getLogger(__name__)
TABLE = "raw_square.locations"
NULL_MARKER = r"\N"
COLUMNS = (
    "square_location_id",
    "payload",
    "ingested_at",
    "orchestrator",
    "pipeline_run_id",
)
QUERY = text("""
    SELECT square_location_id, payload::text AS payload,
           ingested_at, orchestrator, pipeline_run_id
    FROM raw_square.locations
    ORDER BY square_location_id
""")


def run(output_dir: Path) -> None:
    orchestrator, run_id = run_metadata()
    LOGGER.info(
        "table=%s orchestrator=%s pipeline_run_id=%s",
        TABLE, orchestrator, run_id,
    )

    with log_stage(LOGGER, "connect", table=TABLE):
        engine = get_postgres_engine()

    try:
        with log_stage(LOGGER, "export", table=TABLE):
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            output_path = output_dir / f"locations_{timestamp}_{uuid4().hex}.csv"

            temporary_path = None
            row_count = 0
            try:
                with NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    newline="",
                    dir=output_dir,
                    suffix=".tmp",
                    delete=False,
                ) as csv_file:
                    temporary_path = Path(csv_file.name)
                    writer = csv.writer(csv_file)
                    writer.writerow(COLUMNS)

                    with engine.connect() as connection:
                        with connection.execution_options(yield_per=1000).execute(QUERY) as rows:
                            for location_id, payload, ingested_at, source, source_run_id in rows:
                                values = (
                                    location_id,
                                    payload,
                                    ingested_at.astimezone(timezone.utc).isoformat(
                                        sep=" ", timespec="microseconds"
                                    ),
                                    source,
                                    source_run_id,
                                )
                                if NULL_MARKER in values:
                                    raise ValueError("A source value matches the CSV NULL marker.")
                                writer.writerow(
                                    NULL_MARKER if value is None else value for value in values
                                )
                                row_count += 1

                if row_count == 0:
                    raise ValueError(f"{TABLE} is empty. No snapshot was published.")

                temporary_path.replace(output_path)
            finally:
                if temporary_path is not None:
                    temporary_path.unlink(missing_ok=True)

            LOGGER.info("table=%s rows=%d file=%s", TABLE, row_count, output_path.name)
    finally:
        engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()
    run_cli(run, output_dir=args.output_dir)
