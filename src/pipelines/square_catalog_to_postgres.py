from src.square.catalog import list_catalog_items
from src.load.postgres.connection import get_postgres_engine
from src.load.postgres.load_square_catalog import load_square_catalog


def run():
    print("[START] Square catalog → PostgreSQL ingestion")

    # 1. Extract: Square 상품 목록 조회
    items = list_catalog_items()

    # 2. Load: 상품 JSON을 PostgreSQL에 저장
    engine = get_postgres_engine()

    try:
        load_square_catalog(
            items=items,
            engine=engine,
        )
    finally:
        engine.dispose()

    print("[DONE] Square catalog → PostgreSQL ingestion")


if __name__ == "__main__":
    run()