"""Compare one exported GCS product CSV with a full BigQuery raw snapshot.

Install at src/pipelines/validate_products_load.py in the chocolate project.
Read-only: does not load, update, delete, or repair data.
Small-table validator; not intended for append/history tables or large datasets.
"""

import argparse
import csv
import io
import logging
import re
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from time import monotonic


LOGGER = logging.getLogger(__spec__.name if __spec__ else __name__)
NULL_MARKER = "\\N"
SCHEMA = (
    ("id", "STRING"),
    ("product_id", "STRING"),
    ("sku", "STRING"),
    ("product_name", "STRING"),
    ("category", "STRING"),
    ("price", "NUMERIC"),
    ("image_key", "STRING"),
    ("description", "STRING"),
    ("is_best_seller", "BOOLEAN"),
    ("active_status", "BOOLEAN"),
    ("square_catalog_object_id", "STRING"),
    ("created_at", "TIMESTAMP"),
    ("updated_at", "TIMESTAMP"),
    ("square_sync_status", "STRING"),
    ("square_synced_at", "TIMESTAMP"),
    ("square_sync_error", "STRING"),
    ("ingested_at", "TIMESTAMP"),
    ("orchestrator", "STRING"),
    ("pipeline_run_id", "STRING"),
)
COLUMNS = tuple(name for name, _ in SCHEMA)


def normalize(value, field_type, *, from_csv=False):
    """Preserve text exactly; compare decimal values and timestamp instants."""
    if value is None or (from_csv and value == NULL_MARKER):
        return None
    if field_type == "STRING":
        if not isinstance(value, str):
            raise ValueError("Unexpected STRING representation")
        return value
    if field_type == "NUMERIC":
        try:
            number = Decimal(value)
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError("Invalid NUMERIC representation") from None
        if not number.is_finite():
            raise ValueError("Non-finite NUMERIC value")
        return number
    if field_type == "BOOLEAN":
        if isinstance(value, bool):
            return value
        if from_csv and value.lower() in ("true", "false"):
            return value.lower() == "true"
        raise ValueError("Invalid BOOLEAN representation")
    if field_type == "TIMESTAMP":
        try:
            timestamp = datetime.fromisoformat(value) if from_csv else value
            if not isinstance(timestamp, datetime) or timestamp.utcoffset() is None:
                raise ValueError
            return timestamp.astimezone(timezone.utc)
        except (TypeError, ValueError, AttributeError):
            raise ValueError("Invalid timezone-aware TIMESTAMP representation") from None
    raise ValueError("Unsupported field type")


def parse_csv(contents, max_rows):
    reader = csv.reader(io.StringIO(contents, newline=""), strict=True)
    if next(reader, None) != list(COLUMNS):
        raise ValueError("CSV header differs from the expected 19 columns/order")
    records = []
    for record_number, row in enumerate(reader, start=1):
        if record_number > max_rows:
            raise ValueError("CSV exceeds max_rows; use a scalable validator")
        if len(row) != len(SCHEMA):
            raise ValueError(f"CSV record {record_number} has an invalid column count")
        normalized = []
        for value, (name, field_type) in zip(row, SCHEMA):
            try:
                normalized.append(normalize(value, field_type, from_csv=True))
            except ValueError:
                # Record position and column name only; never print source values.
                raise ValueError(
                    f"CSV record {record_number}, column {name}: invalid value format"
                ) from None
        records.append(tuple(normalized))
    if not records:
        raise ValueError("Empty product snapshot rejected; confirm source/export")
    return records


def compare_records(expected, actual):
    """Order independent, duplicate aware, all-column comparison."""
    expected_counts, actual_counts = Counter(expected), Counter(actual)
    missing = sum((expected_counts - actual_counts).values())
    unexpected = sum((actual_counts - expected_counts).values())
    LOGGER.info(
        "stage=compare expected_rows=%d actual_rows=%d "
        "missing_or_changed_rows=%d unexpected_or_changed_rows=%d",
        len(expected), len(actual), missing, unexpected,
    )
    if missing or unexpected:
        raise ValueError(
            f"Snapshot mismatch: expected_rows={len(expected)}, "
            f"actual_rows={len(actual)}, missing_or_changed_rows={missing}, "
            f"unexpected_or_changed_rows={unexpected}"
        )


def run(gcs_uri, table, location, max_rows, max_file_bytes, maximum_bytes_billed):
    from google.cloud import bigquery, storage
    from src.pipelines.run_logging import log_stage, run_metadata

    if not re.fullmatch(r"[a-z][a-z0-9-]*\.[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*", table):
        raise ValueError("Expected project.dataset.table with simple identifiers")
    if not gcs_uri.startswith("gs://"):
        raise ValueError("Expected an exact gs://bucket/object URI")
    bucket, separator, object_name = gcs_uri[5:].partition("/")
    if not bucket or not separator or not object_name or any(c in gcs_uri for c in "*?[]#"):
        raise ValueError("Select one exact GCS object; wildcards are not supported")

    started = monotonic()
    orchestrator, pipeline_run_id = run_metadata()
    LOGGER.info(
        "status=started orchestrator=%s pipeline_run_id=%s table=%s",
        orchestrator, pipeline_run_id, table,
    )
    project = table.split(".")[0]
    with storage.Client(project=project) as gcs, bigquery.Client(project=project) as bq:
        with log_stage(LOGGER, "read_source"):
            blob = gcs.bucket(bucket).blob(object_name)
            blob.reload(timeout=60)
            if blob.size is None or blob.size > max_file_bytes:
                raise ValueError("GCS file exceeds size limit or size is unavailable")
            generation = int(blob.generation)
            contents = blob.download_as_text(
                encoding="utf-8-sig", if_generation_match=generation, timeout=60,
            )
            expected = parse_csv(contents, max_rows)
            LOGGER.info(
                "stage=read_source source_rows=%d source_generation=%s",
                len(expected), generation,
            )

        with log_stage(LOGGER, "check_schema"):
            metadata = bq.get_table(table, timeout=60)
            aliases = {"BOOL": "BOOLEAN", "DECIMAL": "NUMERIC"}
            actual_schema = tuple(
                (field.name, aliases.get(field.field_type, field.field_type))
                for field in metadata.schema
            )
            if metadata.table_type != "TABLE":
                raise ValueError("Expected a native BigQuery table")
            if actual_schema != SCHEMA or any(f.mode != "NULLABLE" for f in metadata.schema):
                raise ValueError("BigQuery schema/order/modes differ from expected schema")
            if metadata.num_rows is not None and metadata.num_rows > max_rows:
                raise ValueError("BigQuery table exceeds max_rows")

        with log_stage(LOGGER, "read_target"):
            columns = ", ".join(f"`{name}`" for name in COLUMNS)
            # Read at most max_rows + 1 to detect growth since get_table().
            query = f"SELECT {columns} FROM `{table}` LIMIT {max_rows + 1}"
            job = bq.query(
                query, location=location,
                job_config=bigquery.QueryJobConfig(
                    use_query_cache=False,
                    maximum_bytes_billed=maximum_bytes_billed,
                ),
                timeout=60,
            )
            actual = [
                tuple(normalize(row[name], field_type) for name, field_type in SCHEMA)
                for row in job.result(timeout=120)
            ]
            if len(actual) > max_rows:
                raise ValueError("BigQuery query exceeds max_rows")
            LOGGER.info("stage=read_target query_job_id=%s", job.job_id)

        with log_stage(LOGGER, "compare"):
            compare_records(expected, actual)

    LOGGER.info(
        "status=completed validation=passed compared_columns=%d "
        "compared_rows=%d pipeline_run_id=%s elapsed_seconds=%.3f",
        len(SCHEMA), len(expected), pipeline_run_id, monotonic() - started,
    )


def positive_integer(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("Must be a positive integer")
    return number


if __name__ == "__main__":
    from src.pipelines.run_logging import run_cli

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gcs-uri", required=True, help="Exact CSV loaded into BigQuery")
    parser.add_argument("--table", default="chocolate-data-platform.raw_online.products")
    parser.add_argument("--location", default="us-east1")
    parser.add_argument("--max-rows", type=positive_integer, default=10_000)
    parser.add_argument("--max-file-bytes", type=positive_integer, default=20_000_000)
    parser.add_argument("--maximum-bytes-billed", type=positive_integer, default=100_000_000)
    run_cli(run, **vars(parser.parse_args()))
