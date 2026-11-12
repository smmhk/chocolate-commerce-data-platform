"""Export and validate Square raw table snapshots."""

import argparse
import csv
import io
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlsplit
from uuid import uuid4

from google.cloud import bigquery, storage
from sqlalchemy import text

from src.load.postgres.connection import get_postgres_engine
from src.pipelines.run_logging import log_stage, run_cli, run_metadata

LOGGER = logging.getLogger(__name__)
PROJECT = "chocolate-data-platform"
NULL_MARKER = r"\N"
METADATA_COLUMNS = ("payload", "ingested_at", "orchestrator", "pipeline_run_id")
TABLE_COLUMNS = {
    "locations": ("square_location_id", *METADATA_COLUMNS),
    "customers": ("square_customer_id", *METADATA_COLUMNS),
    "catalog_objects": ("square_object_id", "object_type", *METADATA_COLUMNS),
    "orders": ("square_order_id", *METADATA_COLUMNS),
}


def export(table_name: str, output_dir: Path) -> None:
    table = f"raw_square.{table_name}"
    columns = TABLE_COLUMNS[table_name]
    select_columns = ", ".join(
        "payload::text AS payload" if column == "payload" else column
        for column in columns
    )
    query = text(f"SELECT {select_columns} FROM {table} ORDER BY {columns[0]}")
    orchestrator, run_id = run_metadata()
    LOGGER.info(
        "table=%s orchestrator=%s pipeline_run_id=%s",
        table, orchestrator, run_id,
    )

    with log_stage(LOGGER, "connect", table=table):
        engine = get_postgres_engine()

    try:
        with log_stage(LOGGER, "export", table=table):
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            output_path = output_dir / f"{table_name}_{timestamp}_{uuid4().hex}.csv"

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
                    writer.writerow(columns)

                    with engine.connect() as connection:
                        with connection.execution_options(yield_per=1000).execute(query) as result:
                            for row in result.mappings():
                                values = dict(row)
                                values["ingested_at"] = row["ingested_at"].astimezone(
                                    timezone.utc
                                ).isoformat(sep=" ", timespec="microseconds")
                                values = tuple(values[column] for column in columns)
                                if NULL_MARKER in values:
                                    raise ValueError("A source value matches the CSV NULL marker.")
                                writer.writerow(
                                    NULL_MARKER if value is None else value for value in values
                                )
                                row_count += 1

                if row_count == 0:
                    raise ValueError(f"{table} is empty. No snapshot was published.")

                temporary_path.replace(output_path)
            finally:
                if temporary_path is not None:
                    temporary_path.unlink(missing_ok=True)

            LOGGER.info("table=%s rows=%d file=%s", table, row_count, output_path.name)
    finally:
        engine.dispose()


def index_rows(rows, key_column):
    indexed = {}
    for row in rows:
        values = dict(row)
        row_id = values.pop(key_column)
        if not row_id or row_id in indexed:
            raise ValueError("A source or target ID is missing or duplicated.")
        if not isinstance(json.loads(values["payload"]), dict):
            raise ValueError("A Square payload is not a JSON object.")
        timestamp = values["ingested_at"]
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("An ingested_at value is missing its timezone.")
        values["ingested_at"] = timestamp.astimezone(timezone.utc)
        indexed[row_id] = values
    return indexed


def read_source(gcs_uri, columns):
    uri = urlsplit(gcs_uri)
    object_name = uri.path.removeprefix("/")
    if uri.scheme != "gs" or not uri.netloc or not object_name:
        raise ValueError("Expected a GCS URI containing a bucket and object name.")

    with storage.Client(project=PROJECT) as client:
        data = client.bucket(uri.netloc).blob(object_name).download_as_bytes()

    reader = csv.reader(io.StringIO(data.decode("utf-8"), newline=""), strict=True)
    if next(reader, None) != list(columns):
        raise ValueError("Square CSV header does not match the expected columns.")

    def parsed_rows():
        for fields in reader:
            values = dict(zip(columns, fields, strict=True))
            values["ingested_at"] = datetime.fromisoformat(values["ingested_at"])
            for column in ("orchestrator", "pipeline_run_id"):
                if values[column] == NULL_MARKER:
                    values[column] = None
            yield values

    return index_rows(parsed_rows(), columns[0])


def validate(table_name: str, gcs_uri: str) -> None:
    table = f"{PROJECT}.raw_square.{table_name}"
    columns = TABLE_COLUMNS[table_name]
    # Catalog descriptions can make a single JSON field exceed the CSV default.
    csv.field_size_limit(10 * 1024 * 1024)
    with log_stage(LOGGER, "read_source"):
        source = read_source(gcs_uri, columns)
        if not source:
            raise ValueError("The source Square CSV contains no data rows.")

    with log_stage(LOGGER, "read_target", table=table):
        query = f"SELECT {', '.join(columns)} FROM `{table}`"
        with bigquery.Client(project=PROJECT, location="us-east1") as client:
            rows = client.query(query).result()
            target = index_rows(rows, columns[0])

    with log_stage(LOGGER, "compare"):
        missing = source.keys() - target.keys()
        extra = target.keys() - source.keys()
        mismatched = sum(
            source[key] != target[key] for key in source.keys() & target.keys()
        )
        LOGGER.info(
            "source_rows=%d target_rows=%d missing_ids=%d extra_ids=%d mismatched_rows=%d",
            len(source), len(target), len(missing), len(extra), mismatched,
        )
        if missing or extra or mismatched:
            raise ValueError("Square CSV and BigQuery table differ.")

    LOGGER.info("validation=passed table=%s rows=%d", table, len(source))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)

    export_parser = subcommands.add_parser("export")
    export_parser.add_argument("--table", choices=TABLE_COLUMNS, required=True)
    export_parser.add_argument("--output-dir", type=Path, default=Path.cwd())

    validate_parser = subcommands.add_parser("validate")
    validate_parser.add_argument("--table", choices=TABLE_COLUMNS, required=True)
    validate_parser.add_argument("--gcs-uri", required=True)

    args = parser.parse_args()
    if args.command == "export":
        run_cli(export, table_name=args.table, output_dir=args.output_dir)
    else:
        run_cli(validate, table_name=args.table, gcs_uri=args.gcs_uri)
