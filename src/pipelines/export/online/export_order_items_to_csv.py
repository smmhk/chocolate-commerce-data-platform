"""Export raw_online.order_items to CSV."""

import argparse
import logging
from pathlib import Path

from src.snapshots.online import export_csv
from src.common.logging import run_cli

LOGGER = logging.getLogger(__name__)
TABLE = "raw_online.order_items"
SCHEMA = (
    ("id", "STRING"),
    ("order_id", "STRING"),
    ("store_id", "STRING"),
    ("product_id", "STRING"),
    ("sku", "STRING"),
    ("product_name", "STRING"),
    ("category", "STRING"),
    ("quantity", "INT64"),
    ("unit_price", "NUMERIC"),
    ("discount_amount", "NUMERIC"),
    ("line_total", "NUMERIC"),
    ("square_catalog_object_id", "STRING"),
    ("created_at", "TIMESTAMP"),
    ("square_line_item_uid", "STRING"),
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
        prefix="order_items_",
        logger=LOGGER,
        require_rows=True,
        normalize_timestamps=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()
    run_cli(run, output_dir=args.output_dir)
