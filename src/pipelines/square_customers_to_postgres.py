from src.square.customers import list_customers
from src.load.postgres.connection import get_postgres_engine
from src.load.postgres.load_square_customers import load_square_customers


def run():
    print("[START] Square customers → PostgreSQL ingestion")

    # 1. Extract: Square 고객 조회
    customers = list_customers()

    # 2. Load: 고객 JSON 원본 저장
    engine = get_postgres_engine()

    try:
        load_square_customers(
            customers=customers,
            engine=engine,
        )
    finally:
        engine.dispose()

    print("[DONE] Square customers → PostgreSQL ingestion")


if __name__ == "__main__":
    run()