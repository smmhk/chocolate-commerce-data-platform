import json

from sqlalchemy import text
from sqlalchemy.engine import Engine


def load_square_orders(
    orders: list[dict],
    engine: Engine,
) -> None:
    """Square 주문 JSON을 PostgreSQL에 Upsert한다."""

    if not orders:
        print("[LOAD] 저장할 Square 주문이 없습니다.")
        return

    query = text("""
        INSERT INTO raw_square.orders (
            square_order_id,
            payload,
            ingested_at
        )
        VALUES (
            :square_order_id,
            CAST(:payload AS JSONB),
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (square_order_id)
        DO UPDATE SET
            payload = EXCLUDED.payload,
            ingested_at = EXCLUDED.ingested_at
    """)

    rows = [
        {
            "square_order_id": order["id"],
            "payload": json.dumps(
                order,
                ensure_ascii=False,
            ),
        }
        for order in orders
    ]

    with engine.begin() as connection:
        connection.execute(query, rows)

    print(
        "[SUCCESS] raw_square.orders "
        f"upsert completed ({len(rows)} orders)"
    )