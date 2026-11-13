"""Run the Square catalog_objects validate pipeline."""

import argparse

from src.common.logging import run_cli
from src.snapshots.square import validate


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gcs-uri", required=True)
    args = parser.parse_args()
    run_cli(validate, table_name="catalog_objects", gcs_uri=args.gcs_uri)
