import json

from src.square.location import list_locations
from src.square.orders import search_orders


def run():
    print("[START] Inspect Square orders")

    # 1. Square 매장 목록 조회
    locations = list_locations()

    print(f"[EXTRACT] total locations: {len(locations)}")

    if not locations:
        print("[INFO] 조회된 매장이 없습니다.")
        return

    orders = []

    # 2. 매장별 주문 조회
    for location in locations:
        location_id = location["id"]
        location_name = location.get("name", "")

        print(
            f"\n[LOCATION] {location_name}"
            f" | ID: {location_id}"
            f" | Status: {location.get('status')}"
        )

        location_orders = search_orders(
            location_ids=[location_id]
        )

        orders.extend(location_orders)

    print(f"\n[SUMMARY] total orders: {len(orders)}")

    if not orders:
        print("[INFO] 조회된 주문이 없습니다.")
        return

    # 3. 첫 주문의 전체 JSON 확인
    print("\n===== FIRST ORDER =====")

    print(
        json.dumps(
            orders[0],
            indent=2,
            ensure_ascii=False,
        )
    )

    # 4. 전체 주문 요약
    print("\n===== ORDER SUMMARY =====")

    for order in orders:
        total = order.get("total_money", {})

        print(
            f"Square Order ID: {order['id']}"
            f" | Reference ID: {order.get('reference_id')}"
            f" | Location: {order.get('location_id')}"
            f" | State: {order.get('state')}"
            f" | Amount: {total.get('amount')}"
            f" | Currency: {total.get('currency')}"
            f" | Line items: {len(order.get('line_items', []))}"
        )

    print("\n[DONE] Inspect Square orders")


if __name__ == "__main__":
    run()