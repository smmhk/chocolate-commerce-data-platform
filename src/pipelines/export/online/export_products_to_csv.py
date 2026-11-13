"""Export raw_online.products to CSV."""

import argparse
import logging

from src.snapshots.online import export_csv
from src.common.logging import run_cli

LOGGER = logging.getLogger(__spec__.name if __spec__ else __name__)
TABLE = "raw_online.products"


def run(output_dir):
    export_csv(
        output_dir, table=TABLE, query=f"SELECT * FROM {TABLE}",
        prefix="products_", logger=LOGGER,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    run_cli(run, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
