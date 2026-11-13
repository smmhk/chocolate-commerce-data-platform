import logging
from datetime import datetime, timezone
from time import monotonic

from src.clients.square.locations import list_locations
from src.clients.square.orders import search_orders
from src.load.postgres.connection import get_postgres_engine
from src.load.postgres.square.upsert_orders import load_square_orders

from src.common.logging import log_stage, run_cli, run_metadata


LOGGER = logging.getLogger(__spec__.name if __spec__ else __name__)


def run():
    ingested_at = datetime.now(timezone.utc)
    orchestrator, pipeline_run_id = run_metadata()
    started = monotonic()
    LOGGER.info(
        "status=started orchestrator=%s pipeline_run_id=%s",
        orchestrator, pipeline_run_id,
    )

    with log_stage(LOGGER, "extract", source="square", resource="locations"):
        locations = list_locations()
        if not locations:
            LOGGER.error("stage=extract resource=locations extracted_rows=0")
            raise RuntimeError("조회된 Square 매장이 없습니다. 매장 설정을 확인해주세요.")

    orders = []
    for location in locations:
        location_id = location["id"]
        with log_stage(LOGGER, "extract", resource="orders", location_id=location_id):
            location_orders = search_orders(location_ids=[location_id])
            LOGGER.info(
                "stage=extract location_id=%s extracted_rows=%d",
                location_id, len(location_orders),
            )
            orders.extend(location_orders)

    LOGGER.info("stage=extract extracted_rows=%d", len(orders))

    with log_stage(LOGGER, "connect"):
        engine = get_postgres_engine()

    try:
        with log_stage(LOGGER, "load", table="raw_square.orders"):
            if not orders:
                LOGGER.warning("stage=load table=raw_square.orders input_rows=0")
            load_square_orders(
                orders=orders,
                engine=engine,
                ingested_at=ingested_at,
                orchestrator=orchestrator,
                pipeline_run_id=pipeline_run_id,
            )
            LOGGER.info("stage=load table=raw_square.orders processed_rows=%d", len(orders))
    finally:
        with log_stage(LOGGER, "dispose"):
            engine.dispose()

    LOGGER.info(
        "status=completed pipeline_run_id=%s elapsed_seconds=%.3f",
        pipeline_run_id, monotonic() - started,
    )


if __name__ == "__main__":
    run_cli(run)
