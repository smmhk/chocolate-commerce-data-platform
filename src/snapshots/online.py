"""Shared CSV export and BigQuery load validation for online raw tables."""

import argparse
import csv
import io
import re
from collections import Counter
import os
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import monotonic

from sqlalchemy import text

from src.load.postgres.connection import get_postgres_engine
from src.common.logging import log_stage, run_metadata



NULL_MARKER = "\\N"


def csv_value(value, normalize_timestamps=False):
    if value is None:
        return NULL_MARKER

    if isinstance(value, datetime):
        if normalize_timestamps:
            return value.astimezone(timezone.utc).isoformat(sep=" ", timespec="microseconds")
        return value.isoformat()

    result = str(value)

    # Prevent actual text from being mistaken for a database NULL.
    if result == NULL_MARKER:
        raise ValueError("A source value conflicts with the CSV NULL marker.")

    return result


def export_csv(
    output_dir, *, table, query, prefix, logger,
    require_rows=False, normalize_timestamps=False,
):
    started = monotonic()
    orchestrator, pipeline_run_id = run_metadata()
    engine = None
    temporary_path = None

    logger.info(
        "status=started orchestrator=%s pipeline_run_id=%s",
        orchestrator,
        pipeline_run_id,
    )

    try:
        with log_stage(logger, "prepare"):
            directory = Path(output_dir)
            directory.mkdir(parents=True, exist_ok=True)

        with log_stage(logger, "connect"):
            engine = get_postgres_engine()

        with log_stage(logger, "export", table=table):
            with engine.connect() as connection:
                result = connection.execution_options(
                    stream_results=True
                ).execute(text(query))

                try:
                    with NamedTemporaryFile(
                        mode="w",
                        encoding="utf-8",
                        newline="",
                        dir=directory,
                        prefix=prefix,
                        suffix=".tmp",
                        delete=False,
                    ) as handle:
                        temporary_path = Path(handle.name)
                        writer = csv.writer(handle)
                        writer.writerow(list(result.keys()))

                        exported_rows = 0

                        for row in result:
                            writer.writerow([csv_value(value, normalize_timestamps) for value in row])
                            exported_rows += 1
                finally:
                    result.close()

            logger.info(
                "stage=export table=%s exported_rows=%d",
                table,
                exported_rows,
            )

        with log_stage(logger, "validate"):
            csv.field_size_limit(10 * 1024 * 1024)
            with temporary_path.open(
                encoding="utf-8", newline=""
            ) as handle:
                reader = csv.reader(handle)
                next(reader)  # Header
                file_rows = sum(1 for _ in reader)

            if require_rows and exported_rows == 0:
                raise ValueError(f"{table} is empty. No snapshot was published.")
            if file_rows != exported_rows:
                raise ValueError("Exported row count and CSV row count differ.")

            file_bytes = temporary_path.stat().st_size

            # Publish the file only after successful validation.
            output_path = temporary_path.with_suffix(".csv")
            os.replace(temporary_path, output_path)
            temporary_path = None

            logger.info(
                "stage=validate file_rows=%d file_bytes=%d output_file=%s",
                file_rows,
                file_bytes,
                output_path,
            )

    finally:
        try:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
        finally:
            if engine is not None:
                with log_stage(logger, "dispose"):
                    engine.dispose()

    logger.info(
        "status=completed pipeline_run_id=%s elapsed_seconds=%.3f",
        pipeline_run_id,
        monotonic() - started,
    )


def normalize(value, field_type, *, from_csv=False):
    """Preserve text exactly; compare decimal values and timestamp instants."""
    if value is None or (from_csv and value == NULL_MARKER):
        return None
    if field_type == "STRING":
        if not isinstance(value, str):
            raise ValueError("Unexpected STRING representation")
        return value
    if field_type == "INT64":
        if from_csv and isinstance(value, str) and re.fullmatch(r"[+-]?[0-9]+", value):
            value = int(value)
        if type(value) is not int or not -(2**63) <= value < 2**63:
            raise ValueError("Invalid INT64 representation")
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


def parse_csv(contents, max_rows, schema):
    csv.field_size_limit(10 * 1024 * 1024)
    reader = csv.reader(io.StringIO(contents, newline=""), strict=True)
    if next(reader, None) != [name for name, _ in schema]:
        raise ValueError("CSV header differs from the expected columns/order")
    records = []
    for record_number, row in enumerate(reader, start=1):
        if record_number > max_rows:
            raise ValueError("CSV exceeds max_rows; use a scalable validator")
        if len(row) != len(schema):
            raise ValueError(f"CSV record {record_number} has an invalid column count")
        normalized = []
        for value, (name, field_type) in zip(row, schema):
            try:
                normalized.append(normalize(value, field_type, from_csv=True))
            except ValueError:
                # Record position and column name only; never print source values.
                raise ValueError(
                    f"CSV record {record_number}, column {name}: invalid value format"
                ) from None
        records.append(tuple(normalized))
    if not records:
        raise ValueError("Empty snapshot rejected; confirm source/export")
    return records


def compare_records(expected, actual, logger):
    """Order independent, duplicate aware, all-column comparison."""
    expected_counts, actual_counts = Counter(expected), Counter(actual)
    missing = sum((expected_counts - actual_counts).values())
    unexpected = sum((actual_counts - expected_counts).values())
    logger.info(
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


def validate_snapshot(
    gcs_uri, *, table, schema, logger,
    location="us-east1", max_rows=10_000, max_file_bytes=20_000_000,
    maximum_bytes_billed=100_000_000,
):
    from google.cloud import bigquery, storage
    from src.common.logging import log_stage, run_metadata

    if not re.fullmatch(r"[a-z][a-z0-9-]*\.[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*", table):
        raise ValueError("Expected project.dataset.table with simple identifiers")
    if not gcs_uri.startswith("gs://"):
        raise ValueError("Expected an exact gs://bucket/object URI")
    bucket, separator, object_name = gcs_uri[5:].partition("/")
    if not bucket or not separator or not object_name or any(c in gcs_uri for c in "*?[]#"):
        raise ValueError("Select one exact GCS object; wildcards are not supported")

    started = monotonic()
    orchestrator, pipeline_run_id = run_metadata()
    logger.info(
        "status=started orchestrator=%s pipeline_run_id=%s table=%s",
        orchestrator, pipeline_run_id, table,
    )
    project = table.split(".")[0]
    with storage.Client(project=project) as gcs, bigquery.Client(project=project) as bq:
        with log_stage(logger, "read_source"):
            blob = gcs.bucket(bucket).blob(object_name)
            blob.reload(timeout=60)
            if blob.size is None or blob.size > max_file_bytes:
                raise ValueError("GCS file exceeds size limit or size is unavailable")
            generation = int(blob.generation)
            contents = blob.download_as_text(
                encoding="utf-8-sig", if_generation_match=generation, timeout=60,
            )
            expected = parse_csv(contents, max_rows, schema)
            logger.info(
                "stage=read_source source_rows=%d source_generation=%s",
                len(expected), generation,
            )

        with log_stage(logger, "check_schema"):
            metadata = bq.get_table(table, timeout=60)
            aliases = {"BOOL": "BOOLEAN", "DECIMAL": "NUMERIC", "INTEGER": "INT64"}
            actual_schema = tuple(
                (field.name, aliases.get(field.field_type, field.field_type))
                for field in metadata.schema
            )
            if metadata.table_type != "TABLE":
                raise ValueError("Expected a native BigQuery table")
            if actual_schema != schema or any(f.mode != "NULLABLE" for f in metadata.schema):
                raise ValueError("BigQuery schema/order/modes differ from expected schema")
            if metadata.num_rows is not None and metadata.num_rows > max_rows:
                raise ValueError("BigQuery table exceeds max_rows")

        with log_stage(logger, "read_target"):
            columns = ", ".join(f"`{name}`" for name, _ in schema)
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
                tuple(normalize(row[name], field_type) for name, field_type in schema)
                for row in job.result(timeout=120)
            ]
            if len(actual) > max_rows:
                raise ValueError("BigQuery query exceeds max_rows")
            logger.info("stage=read_target query_job_id=%s", job.job_id)

        with log_stage(logger, "compare"):
            compare_records(expected, actual, logger)

    logger.info(
        "status=completed validation=passed compared_columns=%d "
        "compared_rows=%d pipeline_run_id=%s elapsed_seconds=%.3f",
        len(schema), len(expected), pipeline_run_id, monotonic() - started,
    )


def positive_integer(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("Must be a positive integer")
    return number
