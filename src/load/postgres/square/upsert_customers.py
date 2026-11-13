import json
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.engine import Engine


def load_square_customers(
    customers: list[dict],
    engine: Engine,
    *,
    ingested_at: datetime,
    orchestrator: str,
    pipeline_run_id: str,
) -> None:
    """Square 고객 JSON과 실행 메타데이터를 PostgreSQL에 Upsert한다."""

    if not customers:
        print("[LOAD] 저장할 Square 고객이 없습니다.")
        return

    query = text("""
        INSERT INTO raw_square.customers (
            square_customer_id,
            payload,
            ingested_at,
            orchestrator,
            pipeline_run_id
        )
        VALUES (
            :square_customer_id,
            CAST(:payload AS JSONB),
            :ingested_at,
            :orchestrator,
            :pipeline_run_id
        )
        ON CONFLICT (square_customer_id)
        DO UPDATE SET
            payload = EXCLUDED.payload,
            ingested_at = EXCLUDED.ingested_at,
            orchestrator = EXCLUDED.orchestrator,
            pipeline_run_id = EXCLUDED.pipeline_run_id
    """)

    rows = [
        {
            "square_customer_id": customer["id"],
            "payload": json.dumps(
                customer,
                ensure_ascii=False,
            ),
            "ingested_at": ingested_at,
            "orchestrator": orchestrator,
            "pipeline_run_id": pipeline_run_id,
        }
        for customer in customers
    ]

    # 모두 성공하면 커밋, 실패하면 이번 변경 전체 롤백
    with engine.begin() as connection:
        connection.execute(query, rows)

    print(
        "[SUCCESS] raw_square.customers "
        f"upsert completed ({len(rows)} customers)"
    )