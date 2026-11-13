import json
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.engine import Engine


def load_square_catalog(
    items: list[dict],
    engine: Engine,
    *,
    ingested_at: datetime,
    orchestrator: str,
    pipeline_run_id: str,
) -> None:
    """Square 상품 JSON과 실행 메타데이터를 PostgreSQL에 Upsert한다."""

    if not items:
        print("[LOAD] 저장할 Square 상품이 없습니다.")
        return

    query = text("""
        INSERT INTO raw_square.catalog_objects (
            square_object_id,
            object_type,
            payload,
            ingested_at,
            orchestrator,
            pipeline_run_id
        )
        VALUES (
            :square_object_id,
            :object_type,
            CAST(:payload AS JSONB),
            :ingested_at,
            :orchestrator,
            :pipeline_run_id
        )
        ON CONFLICT (square_object_id)
        DO UPDATE SET
            object_type = EXCLUDED.object_type,
            payload = EXCLUDED.payload,
            ingested_at = EXCLUDED.ingested_at,
            orchestrator = EXCLUDED.orchestrator,
            pipeline_run_id = EXCLUDED.pipeline_run_id
    """)

    rows = [
        {
            "square_object_id": item["id"],
            "object_type": item["type"],
            "payload": json.dumps(
                item,
                ensure_ascii=False,
            ),
            "ingested_at": ingested_at,
            "orchestrator": orchestrator,
            "pipeline_run_id": pipeline_run_id,
        }
        for item in items
    ]

    # 전체 상품을 하나의 트랜잭션으로 저장
    # 성공하면 커밋, 실패하면 이번 변경 전체 롤백
    with engine.begin() as connection:
        connection.execute(query, rows)

    print(
        "[SUCCESS] raw_square.catalog_objects "
        f"upsert completed ({len(rows)} items)"
    )