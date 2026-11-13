"""Export raw_online.orders to CSV."""

import argparse
import logging
from pathlib import Path

from src.snapshots.online import export_csv
from src.common.logging import run_cli

LOGGER = logging.getLogger(__name__)
TABLE = "raw_online.orders"
SCHEMA = (
    ("id", "STRING"),
    ("order_id", "STRING"),
    ("channel", "STRING"),
    ("store_id", "STRING"),
    ("customer_id", "STRING"),
    ("customer_type", "STRING"),
    ("contact_first_name", "STRING"),
    ("contact_last_name", "STRING"),
    ("contact_email", "STRING"),
    ("contact_phone", "STRING"),
    ("shipping_address_line1", "STRING"),
    ("shipping_address_line2", "STRING"),
    ("shipping_city", "STRING"),
    ("shipping_province", "STRING"),
    ("shipping_postal_code", "STRING"),
    ("shipping_country", "STRING"),
    ("order_status", "STRING"),
    ("subtotal", "NUMERIC"),
    ("discount_type", "STRING"),
    ("discount_amount", "NUMERIC"),
    ("discount_reason", "STRING"),
    ("tax_rate", "NUMERIC"),
    ("tax_amount", "NUMERIC"),
    ("shipping_amount", "NUMERIC"),
    ("total_amount", "NUMERIC"),
    ("payment_method", "STRING"),
    ("item_count", "INT64"),
    ("created_at", "TIMESTAMP"),
    ("completed_at", "TIMESTAMP"),
    ("square_order_id", "STRING"),
    ("square_customer_id", "STRING"),
    ("square_location_id", "STRING"),
    ("square_sync_status", "STRING"),
    ("square_synced_at", "TIMESTAMP"),
    ("square_sync_error", "STRING"),
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
        prefix="orders_",
        logger=LOGGER,
        require_rows=True,
        normalize_timestamps=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()
    run_cli(run, output_dir=args.output_dir)
