"""Export raw_online.customer_addresses to CSV."""

import argparse
import logging
from pathlib import Path

from src.snapshots.online import export_csv
from src.common.logging import run_cli

LOGGER = logging.getLogger(__name__)
TABLE = "raw_online.customer_addresses"
SCHEMA = (
    ("id", "STRING"),
    ("customer_id", "STRING"),
    ("label", "STRING"),
    ("address_line1", "STRING"),
    ("address_line2", "STRING"),
    ("city", "STRING"),
    ("province", "STRING"),
    ("postal_code", "STRING"),
    ("country", "STRING"),
    ("is_default", "BOOLEAN"),
    ("created_at", "TIMESTAMP"),
    ("square_customer_id", "STRING"),
    ("ingested_at", "TIMESTAMP"),
    ("orchestrator", "STRING"),
    ("pipeline_run_id", "STRING"),
)
COLUMNS = tuple(name for name, _ in SCHEMA)


def run(output_dir: Path) -> None:
    export_csv(
        output_dir,
        table=TABLE,
        query=f"SELECT {', '.join(COLUMNS)} FROM {TABLE}",
        prefix="customer_addresses_",
        logger=LOGGER,
        require_rows=True,
        normalize_timestamps=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()
    run_cli(run, output_dir=args.output_dir)
