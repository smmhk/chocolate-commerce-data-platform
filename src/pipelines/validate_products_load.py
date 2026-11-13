"""Validate the GCS Products CSV against BigQuery."""

import argparse
import logging

from src.pipelines.online_raw_snapshot import positive_integer, validate_snapshot
from src.pipelines.run_logging import run_cli

LOGGER = logging.getLogger(__spec__.name if __spec__ else __name__)
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


def run(gcs_uri, table, location, max_rows, max_file_bytes, maximum_bytes_billed):
    validate_snapshot(
        gcs_uri, table=table, schema=SCHEMA, logger=LOGGER, location=location,
        max_rows=max_rows, max_file_bytes=max_file_bytes,
        maximum_bytes_billed=maximum_bytes_billed,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gcs-uri", required=True, help="Exact CSV loaded into BigQuery")
    parser.add_argument("--table", default="chocolate-data-platform.raw_online.products")
    parser.add_argument("--location", default="us-east1")
    parser.add_argument("--max-rows", type=positive_integer, default=10_000)
    parser.add_argument("--max-file-bytes", type=positive_integer, default=20_000_000)
    parser.add_argument("--maximum-bytes-billed", type=positive_integer, default=100_000_000)
    run_cli(run, **vars(parser.parse_args()))
