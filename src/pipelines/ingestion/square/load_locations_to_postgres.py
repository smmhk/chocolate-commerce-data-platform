import logging
from datetime import datetime, timezone
from time import monotonic

from src.clients.square.locations import list_locations
from src.load.postgres.connection import get_postgres_engine
from src.load.postgres.square.upsert_locations import load_square_locations

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

    LOGGER.info("stage=extract extracted_rows=%d", len(locations))

    with log_stage(LOGGER, "connect"):
        engine = get_postgres_engine()

    try:
        with log_stage(LOGGER, "load", table="raw_square.locations"):
            if not locations:
                LOGGER.warning("stage=load table=raw_square.locations input_rows=0")
            load_square_locations(
                locations=locations,
                engine=engine,
                ingested_at=ingested_at,
                orchestrator=orchestrator,
                pipeline_run_id=pipeline_run_id,
            )
            LOGGER.info("stage=load table=raw_square.locations processed_rows=%d", len(locations))
    finally:
        with log_stage(LOGGER, "dispose"):
            engine.dispose()

    LOGGER.info(
        "status=completed pipeline_run_id=%s elapsed_seconds=%.3f",
        pipeline_run_id, monotonic() - started,
    )


if __name__ == "__main__":
    run_cli(run)
