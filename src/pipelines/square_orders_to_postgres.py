from src.square.location import list_locations
from src.square.orders import search_orders
from src.load.postgres.connection import get_postgres_engine
from src.load.postgres.load_square_orders import load_square_orders


def run():
    print("[START] Square orders → PostgreSQL ingestion")

    locations = list_locations()

    if not locations:
        raise RuntimeError(
            "조회된 Square 매장이 없습니다. 매장 설정을 확인해주세요."
        )

    orders = []

    for location in locations:
        print(
            f"\n[LOCATION] {location.get('name')}"
            f" | ID: {location['id']}"
        )

        location_orders = search_orders(
            location_ids=[location["id"]]
        )

        orders.extend(location_orders)

    print(f"\n[SUMMARY] total orders: {len(orders)}")

    engine = get_postgres_engine()

    try:
        load_square_orders(
            orders=orders,
            engine=engine,
        )
    finally:
        engine.dispose()

    print("[DONE] Square orders → PostgreSQL ingestion")


if __name__ == "__main__":
    run()