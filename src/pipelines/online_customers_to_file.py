"""Export raw_online.customers to a UTF-8 CSV snapshot."""

import argparse
import logging
from pathlib import Path

from src.pipelines.online_raw_snapshot import export_csv
from src.pipelines.run_logging import run_cli

LOGGER = logging.getLogger(__name__)
TABLE = "raw_online.customers"
COLUMNS = (
    "id",
    "customer_number",
    "user_id",
    "email",
    "first_name",
    "last_name",
    "phone",
    "customer_type",
    "square_customer_id",
    "created_at",
    "updated_at",
    "signup_channel",
    "square_sync_status",
    "square_synced_at",
    "square_sync_error",
    "ingested_at",
    "orchestrator",
    "pipeline_run_id",
)
TIMESTAMP_COLUMNS = frozenset({"created_at", "updated_at", "square_synced_at", "ingested_at"})


def run(output_dir: Path) -> None:
    export_csv(
        output_dir,
        table=TABLE,
        query=f"SELECT {', '.join(COLUMNS)} FROM {TABLE}",
        prefix="customers_",
        logger=LOGGER,
        require_rows=True,
        normalize_timestamps=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()
    run_cli(run, output_dir=args.output_dir)
