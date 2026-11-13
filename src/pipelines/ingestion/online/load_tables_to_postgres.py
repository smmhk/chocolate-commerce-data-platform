import argparse
import logging
from datetime import datetime, timezone
from time import monotonic

from src.extract.online.read_source_tables import load_online_data
from src.transform.online.select_channel_records import filter_online_data
from src.load.postgres.connection import get_postgres_engine
from src.load.postgres.online.replace_table import load_dataframe_to_postgres

from src.common.logging import log_stage, run_cli, run_metadata


LOGGER = logging.getLogger(__spec__.name if __spec__ else __name__)


LOAD_ORDER = (
    "products",
    "customers",
    "customer_addresses",
    "orders",
    "order_items",
)


def run(tables=None):
    selected_tables = LOAD_ORDER if tables is None else tables
    tables_to_load = [name for name in LOAD_ORDER if name in selected_tables]

    ingested_at = datetime.now(timezone.utc)
    orchestrator, pipeline_run_id = run_metadata()
    started = monotonic()
    LOGGER.info(
        "status=started orchestrator=%s pipeline_run_id=%s tables=%s",
        orchestrator, pipeline_run_id, ",".join(tables_to_load),
    )

    with log_stage(LOGGER, "extract", source="online_csv"):
        source_data = load_online_data()

    with log_stage(LOGGER, "transform"):
        online_data = filter_online_data(source_data)
        for table_name in tables_to_load:
            LOGGER.info(
                "stage=transform table=%s input_rows=%d output_rows=%d",
                table_name, len(source_data[table_name]), len(online_data[table_name]),
            )

    with log_stage(LOGGER, "connect"):
        engine = get_postgres_engine()

    try:
        for table_name in tables_to_load:
            with log_stage(LOGGER, "load", table=f"raw_online.{table_name}"):
                df = online_data[table_name].copy()
                df["ingested_at"] = ingested_at
                df["orchestrator"] = orchestrator
                df["pipeline_run_id"] = pipeline_run_id

                if df.empty:
                    LOGGER.warning("stage=load table=raw_online.%s input_rows=0", table_name)

                load_dataframe_to_postgres(df=df, table_name=table_name, engine=engine)
                LOGGER.info("stage=load table=raw_online.%s loaded_rows=%d", table_name, len(df))
    finally:
        with log_stage(LOGGER, "dispose"):
            engine.dispose()

    LOGGER.info(
        "status=completed pipeline_run_id=%s elapsed_seconds=%.3f",
        pipeline_run_id, monotonic() - started,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="온라인 CSV 데이터를 PostgreSQL에 적재합니다."
    )

    parser.add_argument(
        "--tables",
        nargs="+",
        choices=LOAD_ORDER,
        default=None,
        help="적재할 테이블 이름. 생략하면 전체를 적재합니다.",
    )

    args = parser.parse_args()
    run_cli(run, tables=args.tables)
