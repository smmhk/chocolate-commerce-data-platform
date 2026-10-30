import json
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.engine import Engine


def load_square_locations(
    locations: list[dict],
    engine: Engine,
    *,
    ingested_at: datetime,
    orchestrator: str,
    pipeline_run_id: str,
) -> None:
    """Square 매장 JSON과 실행 메타데이터를 PostgreSQL에 Upsert한다."""

    if not locations:
        print("[LOAD] 저장할 Square 매장이 없습니다.")
        return

    query = text("""
        INSERT INTO raw_square.locations (
            square_location_id,
            payload,
            ingested_at,
            orchestrator,
            pipeline_run_id
        )
        VALUES (
            :square_location_id,
            CAST(:payload AS JSONB),
            :ingested_at,
            :orchestrator,
            :pipeline_run_id
        )
        ON CONFLICT (square_location_id)
        DO UPDATE SET
            payload = EXCLUDED.payload,
            ingested_at = EXCLUDED.ingested_at,
            orchestrator = EXCLUDED.orchestrator,
            pipeline_run_id = EXCLUDED.pipeline_run_id
    """)

    rows = [
        {
            "square_location_id": location["id"],
            "payload": json.dumps(
                location,
                ensure_ascii=False,
            ),
            "ingested_at": ingested_at,
            "orchestrator": orchestrator,
            "pipeline_run_id": pipeline_run_id,
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