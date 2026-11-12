"""Compare a Locations CSV snapshot in GCS with the BigQuery raw table."""

import argparse

from src.pipelines.run_logging import run_cli
from src.pipelines.square_raw_snapshot import validate


def run(gcs_uri: str) -> None:
    validate(table_name="locations", gcs_uri=gcs_uri)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gcs-uri", required=True)
    args = parser.parse_args()
    run_cli(run, gcs_uri=args.gcs_uri)
