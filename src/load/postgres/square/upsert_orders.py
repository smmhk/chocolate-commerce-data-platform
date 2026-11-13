import json
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.engine import Engine


def load_square_orders(
    orders: list[dict],
    engine: Engine,
    *,
    ingested_at: datetime,
    orchestrator: str,
    pipeline_run_id: str,
) -> None:
    """Square 주문 JSON과 실행 메타데이터를 PostgreSQL에 Upsert한다."""

    if not orders:
        print("[LOAD] 저장할 Square 주문이 없습니다.")
        return

    query = text("""
        INSERT INTO raw_square.orders (
            square_order_id,
            payload,
            ingested_at,
            orchestrator,
            pipeline_run_id
        )
        VALUES (
            :square_order_id,
            CAST(:payload AS JSONB),
            :ingested_at,
            :orchestrator,
            :pipeline_run_id
        )
        ON CONFLICT (square_order_id)
        DO UPDATE SET
            payload = EXCLUDED.payload,
            ingested_at = EXCLUDED.ingested_at,
            orchestrator = EXCLUDED.orchestrator,
            pipeline_run_id = EXCLUDED.pipeline_run_id
    """)

    rows = [
        {
            "square_order_id": order["id"],
            "payload": json.dumps(
                order,
                ensure_ascii=False,
            ),
            "ingested_at": ingested_at,
            "orchestrator": orchestrator,
            "pipeline_run_id": pipeline_run_id,
        }
        for order in orders
    ]

    # 전체 주문 저장 성공 시 커밋, 실패 시 이번 변경 롤백
    with engine.begin() as connection:
        connection.execute(query, rows)

    print(
        "[SUCCESS] raw_square.orders "
        f"upsert completed ({len(rows)} orders)"
    )