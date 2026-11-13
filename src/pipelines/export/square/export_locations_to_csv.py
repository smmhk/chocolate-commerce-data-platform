"""Export a PostgreSQL snapshot of raw_square.locations to UTF-8 CSV."""

import argparse
from pathlib import Path

from src.common.logging import run_cli
from src.snapshots.square import export


def run(output_dir: Path) -> None:
    export(table_name="locations", output_dir=output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()
    run_cli(run, output_dir=args.output_dir)
