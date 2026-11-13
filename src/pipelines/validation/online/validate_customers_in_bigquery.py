"""Validate the GCS Online Customers CSV against BigQuery."""

import argparse
import logging

from src.pipelines.export.online.export_customers_to_csv import COLUMNS, TABLE, TIMESTAMP_COLUMNS
from src.snapshots.online import validate_snapshot
from src.common.logging import run_cli

LOGGER = logging.getLogger(__name__)
SCHEMA = tuple(
    (column, "TIMESTAMP" if column in TIMESTAMP_COLUMNS else "STRING")
    for column in COLUMNS
)


def run(gcs_uri: str) -> None:
    validate_snapshot(
        gcs_uri, table=f"chocolate-data-platform.{TABLE}", schema=SCHEMA, logger=LOGGER,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gcs-uri", required=True)
    args = parser.parse_args()
    run_cli(run, gcs_uri=args.gcs_uri)
