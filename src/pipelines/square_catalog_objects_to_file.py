"""Run the Square catalog_objects export pipeline."""

import argparse
from pathlib import Path

from src.pipelines.run_logging import run_cli
from src.pipelines.square_raw_snapshot import export


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()
    run_cli(export, table_name="catalog_objects", output_dir=args.output_dir)
