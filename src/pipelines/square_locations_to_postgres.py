from src.square.location import list_locations
from src.load.postgres.connection import get_postgres_engine
from src.load.postgres.load_square_locations import load_square_locations


def run():
    print("[START] Square locations → PostgreSQL ingestion")

    # 1. Extract: Square 매장 목록 조회
    locations = list_locations()

    print(
        f"[EXTRACT] total locations: {len(locations)}"
    )

    # 2. Load: 매장 JSON 원본 저장
    engine = get_postgres_engine()

    try:
        load_square_locations(
            locations=locations,
            engine=engine,
        )
    finally:
        engine.dispose()

    print("[DONE] Square locations → PostgreSQL ingestion")


if __name__ == "__main__":
    run()