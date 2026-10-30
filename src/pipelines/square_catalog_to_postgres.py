import os
from datetime import datetime, timezone
from uuid import uuid4

from src.square.catalog import list_catalog_items
from src.load.postgres.connection import get_postgres_engine
from src.load.postgres.load_square_catalog import load_square_catalog


def run():
    print("[START] Square catalog → PostgreSQL ingestion")

    # 1. Extract: Square 상품 목록 조회
    items = list_catalog_items()

    print(f"[EXTRACT] total items: {len(items)}")

    # 2. 실행 메타데이터 생성
    ingested_at = datetime.now(timezone.utc)
    orchestrator = os.getenv("PIPELINE_ORCHESTRATOR", "local")
    pipeline_run_id = (
        os.getenv("PIPELINE_RUN_ID") or str(uuid4())
    )

    print(f"[RUN] orchestrator: {orchestrator}")
    print(f"[RUN] pipeline_run_id: {pipeline_run_id}")
    print(f"[RUN] ingested_at: {ingested_at.isoformat()}")

    # 3. Load: 상품 JSON과 메타데이터 저장
    engine = get_postgres_engine()

    try:
        load_square_catalog(
            items=items,
            engine=engine,
            ingested_at=ingested_at,
            orchestrator=orchestrator,
            pipeline_run_id=pipeline_run_id,
        )
    finally:
        engine.dispose()

    print("[DONE] Square catalog → PostgreSQL ingestion")


if __name__ == "__main__":
    run()