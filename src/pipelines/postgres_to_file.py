import argparse
import csv
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import monotonic

from sqlalchemy import text

from src.load.postgres.connection import get_postgres_engine
from src.pipelines.run_logging import log_stage, run_cli, run_metadata


LOGGER = logging.getLogger(__spec__.name if __spec__ else __name__)

NULL_MARKER = "\\N"


def csv_value(value):
    if value is None:
        return NULL_MARKER

    if isinstance(value, datetime):
        return value.isoformat()

    result = str(value)

    # Prevent actual text from being mistaken for a database NULL.
    if result == NULL_MARKER:
        raise ValueError("A source value conflicts with the CSV NULL marker.")

    return result


def run(output_dir):
    started = monotonic()
    orchestrator, pipeline_run_id = run_metadata()
    engine = None
    temporary_path = None

    LOGGER.info(
        "status=started orchestrator=%s pipeline_run_id=%s",
        orchestrator,
        pipeline_run_id,
    )

    try:
        with log_stage(LOGGER, "prepare"):
            directory = Path(output_dir)
            directory.mkdir(parents=True, exist_ok=True)

        with log_stage(LOGGER, "connect"):
            engine = get_postgres_engine()

        with log_stage(LOGGER, "export", table="raw_online.products"):
            with engine.connect() as connection:
                result = connection.execution_options(
                    stream_results=True
                ).execute(text("SELECT * FROM raw_online.products"))

                try:
                    with NamedTemporaryFile(
                        mode="w",
                        encoding="utf-8",
                        newline="",
                        dir=directory,
                        prefix="products_",
                        suffix=".tmp",
                        delete=False,
                    ) as handle:
                        temporary_path = Path(handle.name)
                        writer = csv.writer(handle)
                        writer.writerow(list(result.keys()))

                        exported_rows = 0

                        for row in result:
                            writer.writerow([csv_value(value) for value in row])
                            exported_rows += 1
                finally:
                    result.close()

            LOGGER.info(
                "stage=export table=raw_online.products exported_rows=%d",
                exported_rows,
            )

        with log_stage(LOGGER, "validate"):
            with temporary_path.open(
                encoding="utf-8", newline=""
            ) as handle:
                reader = csv.reader(handle)
                next(reader)  # Header
                file_rows = sum(1 for _ in reader)

            if file_rows != exported_rows:
                raise ValueError("Exported row count and CSV row count differ.")

            file_bytes = temporary_path.stat().st_size

            # Publish the file only after successful validation.
            output_path = temporary_path.with_suffix(".csv")
            os.replace(temporary_path, output_path)
            temporary_path = None

            LOGGER.info(
                "stage=validate file_rows=%d file_bytes=%d output_file=%s",
                file_rows,
                file_bytes,
                output_path,
            )

    finally:
        try:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
        finally:
            if engine is not None:
                with log_stage(LOGGER, "dispose"):
                    engine.dispose()

    LOGGER.info(
        "status=completed pipeline_run_id=%s elapsed_seconds=%.3f",
        pipeline_run_id,
        monotonic() - started,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="PostgreSQL 상품 데이터를 CSV로 내보냅니다."
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="CSV 파일을 저장할 쓰기 가능한 디렉터리",
    )

    args = parser.parse_args()
    run_cli(run, output_dir=args.output_dir)