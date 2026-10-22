from src.extract.online.load_online_data import load_online_data
from src.transform.online.filter_online_data import filter_online_data
from src.load.postgres.connection import get_postgres_engine
from src.load.postgres.load_table import load_dataframe_to_postgres


# =========================================================
# PostgreSQL 적재 순서
# =========================================================

LOAD_ORDER = (
    "products",
    "customers",
    "customer_addresses",
    "orders",
    "order_items",
)


# =========================================================
# Online → PostgreSQL Pipeline
# =========================================================

def run():
    print("[START] Online → PostgreSQL ingestion")

    # 1. Extract: 원본 CSV 5개 읽기
    source_data = load_online_data()

    # 2. Transform: 온라인 데이터 선별
    online_data = filter_online_data(source_data)

    # 3. Load: PostgreSQL에 저장
    engine = get_postgres_engine()

    try:
        for table_name in LOAD_ORDER:
            df = online_data[table_name]

            load_dataframe_to_postgres(
                df=df,
                table_name=table_name,
                engine=engine,
            )

            print(
                f"[LOAD] {table_name} rows: {len(df)}"
            )

    finally:
        # 성공 또는 오류 여부와 관계없이 연결 풀 정리
        engine.dispose()

    print("[DONE] Online → PostgreSQL ingestion")


# =========================================================
# Run Pipeline
# =========================================================

if __name__ == "__main__":
    run()