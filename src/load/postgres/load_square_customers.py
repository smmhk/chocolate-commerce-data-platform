import json

from sqlalchemy import text
from sqlalchemy.engine import Engine


def load_square_customers(
    customers: list[dict],
    engine: Engine,
) -> None:
    """Square 고객 JSON을 PostgreSQL에 Upsert한다."""

    if not customers:
        print("[LOAD] 저장할 Square 고객이 없습니다.")
        return

    query = text("""
        INSERT INTO raw_square.customers (
            square_customer_id,
            payload,
            ingested_at
        )
        VALUES (
            :square_customer_id,
            CAST(:payload AS JSONB),
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (square_customer_id)
        DO UPDATE SET
            payload = EXCLUDED.payload,
            ingested_at = EXCLUDED.ingested_at
    """)

    rows = [
        {
            "square_customer_id": customer["id"],
            "payload": json.dumps(
                customer,
                ensure_ascii=False,
            ),
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