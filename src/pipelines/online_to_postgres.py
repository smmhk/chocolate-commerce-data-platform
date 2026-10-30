import argparse
import os
from datetime import datetime, timezone
from uuid import uuid4

from src.extract.online.load_online_data import load_online_data
from src.transform.online.filter_online_data import filter_online_data
from src.load.postgres.connection import get_postgres_engine
from src.load.postgres.load_table import load_dataframe_to_postgres


LOAD_ORDER = (
    "products",
    "customers",
    "customer_addresses",
    "orders",
    "order_items",
)


def run(tables=None):
    # 입력 순서와 관계없이 기존 적재 순서를 유지
    selected_tables = (
        LOAD_ORDER if tables is None else tables
    )
    tables_to_load = [
        name for name in LOAD_ORDER
        if name in selected_tables
    ]

    print("[START] Online → PostgreSQL ingestion")
    print(f"[INFO] Tables to load: {', '.join(tables_to_load)}")

    # 기존 추출·변환 로직 재사용
    source_data = load_online_data()
    online_data = filter_online_data(source_data)

    # 한 번의 파이프라인 실행에 공통으로 사용할 메타데이터
    ingested_at = datetime.now(timezone.utc)
    orchestrator = os.getenv("PIPELINE_ORCHESTRATOR", "local")
    pipeline_run_id = (
        os.getenv("PIPELINE_RUN_ID") or str(uuid4())
    )

    print(f"[RUN] orchestrator: {orchestrator}")
    print(f"[RUN] pipeline_run_id: {pipeline_run_id}")
    print(f"[RUN] ingested_at: {ingested_at.isoformat()}")

    engine = get_postgres_engine()

    try:
        for table_name in tables_to_load:
            
            df = online_data[table_name].copy()

            df["ingested_at"] = ingested_at
            df["orchestrator"] = orchestrator
            df["pipeline_run_id"] = pipeline_run_id

            load_dataframe_to_postgres(
                df=df,
                table_name=table_name,
                engine=engine,
            )

            print(
                f"[LOAD] {table_name} rows: {len(df)}"
            )
    finally:
        engine.dispose()

    print("[DONE] Online → PostgreSQL ingestion")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="온라인 CSV 데이터를 PostgreSQL에 적재합니다."
    )

    parser.add_argument(
        "--tables",
        nargs="+",
        choices=LOAD_ORDER,
        default=None,
        help="적재할 테이블 이름. 생략하면 전체를 적재합니다.",
    )

    args = parser.parse_args()
    run(tables=args.tables)