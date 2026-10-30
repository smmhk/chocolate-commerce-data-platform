import os
from datetime import datetime, timezone
from uuid import uuid4

from src.square.location import list_locations
from src.square.orders import search_orders
from src.load.postgres.connection import get_postgres_engine
from src.load.postgres.load_square_orders import load_square_orders


def run():
    print("[START] Square orders → PostgreSQL ingestion")

    # 1. Extract: 매장 목록 조회
    locations = list_locations()

    if not locations:
        raise RuntimeError(
            "조회된 Square 매장이 없습니다. 매장 설정을 확인해주세요."
        )

    # 2. 매장별 주문 조회
    orders = []

    for location in locations:
        print(
            f"\n[LOCATION] {location.get('name')}"
            f" | ID: {location['id']}"
        )

        location_orders = search_orders(
            location_ids=[location["id"]]
        )

        orders.extend(location_orders)

    print(f"\n[SUMMARY] total orders: {len(orders)}")

    # 3. 이번 실행에 공통으로 사용할 메타데이터
    ingested_at = datetime.now(timezone.utc)
    orchestrator = os.getenv("PIPELINE_ORCHESTRATOR", "local")
    pipeline_run_id = (
        os.getenv("PIPELINE_RUN_ID") or str(uuid4())
    )

    print(f"[RUN] orchestrator: {orchestrator}")
    print(f"[RUN] pipeline_run_id: {pipeline_run_id}")
    print(f"[RUN] ingested_at: {ingested_at.isoformat()}")

    # 4. Load: 주문 JSON과 메타데이터 저장
    engine = get_postgres_engine()

    try:
        load_square_orders(
            orders=orders,
            engine=engine,
            ingested_at=ingested_at,
            orchestrator=orchestrator,
            pipeline_run_id=pipeline_run_id,
        )
    finally:
        engine.dispose()

    print("[DONE] Square orders → PostgreSQL ingestion")


if __name__ == "__main__":
    run()