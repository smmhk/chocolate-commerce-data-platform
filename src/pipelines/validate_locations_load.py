"""Compare a Locations CSV snapshot in GCS with the BigQuery raw table."""

import argparse
import csv
import io
import json
import logging
from datetime import datetime, timezone
from urllib.parse import urlsplit

from google.cloud import bigquery, storage

from src.pipelines.run_logging import log_stage, run_cli

LOGGER = logging.getLogger(__name__)
PROJECT = "chocolate-data-platform"
TABLE = f"{PROJECT}.raw_square.locations"
COLUMNS = (
    "square_location_id",
    "payload",
    "ingested_at",
    "orchestrator",
    "pipeline_run_id",
)
NULL_MARKER = r"\N"


def index_rows(rows):
    indexed = {}
    for location_id, payload, timestamp, orchestrator, run_id in rows:
        if not location_id or location_id in indexed:
            raise ValueError("A location ID is missing or duplicated.")
        if not isinstance(json.loads(payload), dict):
            raise ValueError("A location payload is not a JSON object.")
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("An ingested_at value is missing its timezone.")
        indexed[location_id] = (
            payload, timestamp.astimezone(timezone.utc), orchestrator, run_id
        )
    return indexed


def read_source(gcs_uri):
    uri = urlsplit(gcs_uri)
    object_name = uri.path.removeprefix("/")
    if uri.scheme != "gs" or not uri.netloc or not object_name:
        raise ValueError("Expected a GCS URI containing a bucket and object name.")

    with storage.Client(project=PROJECT) as client:
        data = client.bucket(uri.netloc).blob(object_name).download_as_bytes()

    reader = csv.reader(io.StringIO(data.decode("utf-8"), newline=""), strict=True)
    if next(reader, None) != list(COLUMNS):
        raise ValueError("Locations CSV header does not match the expected columns.")

    def parsed_rows():
        for location_id, payload, timestamp, orchestrator, run_id in reader:
            yield (
                location_id, payload, datetime.fromisoformat(timestamp),
                None if orchestrator == NULL_MARKER else orchestrator,
                None if run_id == NULL_MARKER else run_id,
            )

    return index_rows(parsed_rows())


def run(gcs_uri):
    with log_stage(LOGGER, "read_source"):
        source = read_source(gcs_uri)
        if not source:
            raise ValueError("The source Locations CSV contains no data rows.")

    with log_stage(LOGGER, "read_target", table=TABLE):
        query = f"SELECT {', '.join(COLUMNS)} FROM `{TABLE}`"
        with bigquery.Client(project=PROJECT, location="us-east1") as client:
            rows = client.query(query).result()
            target = index_rows(tuple(row[column] for column in COLUMNS) for row in rows)

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
            raise ValueError("Locations CSV and BigQuery table differ.")

    LOGGER.info("validation=passed table=%s rows=%d", TABLE, len(source))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gcs-uri", required=True)
    args = parser.parse_args()
    run_cli(run, gcs_uri=args.gcs_uri)
