import json

from sqlalchemy import text
from sqlalchemy.engine import Engine


def load_square_locations(
    locations: list[dict],
    engine: Engine,
) -> None:
    """Square 매장 JSON을 PostgreSQL에 Upsert한다."""

    if not locations:
        print("[LOAD] 저장할 Square 매장이 없습니다.")
        return

    query = text("""
        INSERT INTO raw_square.locations (
            square_location_id,
            payload,
            ingested_at
        )
        VALUES (
            :square_location_id,
            CAST(:payload AS JSONB),
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (square_location_id)
        DO UPDATE SET
            payload = EXCLUDED.payload,
            ingested_at = EXCLUDED.ingested_at
    """)

    rows = [
        {
            "square_location_id": location["id"],
            "payload": json.dumps(
                location,
                ensure_ascii=False,
            ),
        }
        for location in locations
    ]

    # 전체 매장 저장 성공 시 커밋, 실패 시 이번 변경 롤백
    with engine.begin() as connection:
        connection.execute(query, rows)

    print(
        "[SUCCESS] raw_square.locations "
        f"upsert completed ({len(rows)} locations)"
    )