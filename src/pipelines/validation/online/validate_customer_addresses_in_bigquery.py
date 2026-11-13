"""Validate the GCS customer_addresses snapshot against BigQuery."""

import argparse
import logging

from src.pipelines.export.online.export_customer_addresses_to_csv import SCHEMA, TABLE
from src.snapshots.online import validate_snapshot
from src.common.logging import run_cli

LOGGER = logging.getLogger(__name__)


def run(gcs_uri: str) -> None:
    validate_snapshot(
        gcs_uri, table=f"chocolate-data-platform.{TABLE}", schema=SCHEMA, logger=LOGGER,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gcs-uri", required=True)
    args = parser.parse_args()
    run_cli(run, gcs_uri=args.gcs_uri)
