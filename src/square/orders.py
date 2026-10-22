import requests

from src.square.client import headers


def create_order(payload):
    url = "https://connect.squareupsandbox.com/v2/orders"

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            f"Square 주문 생성 실패 "
            f"({response.status_code}): {response.text}"
        )

    result = response.json()

    if result.get("errors"):
        raise RuntimeError(
            f"Square 주문 생성 오류: {result['errors']}"
        )

    square_order = result.get("order")

    if not square_order or not square_order.get("id"):
        raise RuntimeError(
            f"응답에서 Square 주문 ID를 찾을 수 없습니다: {result}"
        )

    return square_order

def search_orders(location_ids: list[str]) -> list[dict]:
    """지정한 Square 매장의 주문을 모든 페이지에서 조회한다."""

    if not location_ids or len(location_ids) > 10:
        raise ValueError(
            "Square location ID를 1~10개 지정해주세요."
        )

    url = "https://connect.squareupsandbox.com/v2/orders/search"

    orders = []
    cursor = None
    page = 1

    while True:
        body = {
            "location_ids": location_ids,
            "limit": 100,
            "return_entries": False,
        }

        if cursor:
            body["cursor"] = cursor

        response = requests.post(
            url,
            headers=headers,
            json=body,
            timeout=30,
        )

        if not response.ok:
            raise RuntimeError(
                f"Square 주문 조회 실패 "
                f"(HTTP {response.status_code}): "
                f"{response.text}"
            )

        data = response.json()

        if data.get("errors"):
            raise RuntimeError(
                f"Square 주문 조회 오류: {data['errors']}"
            )

        page_orders = data.get("orders", [])
        orders.extend(page_orders)

        print(
            f"[EXTRACT] page {page}: "
            f"{len(page_orders)} orders"
        )

        cursor = data.get("cursor")

        if not cursor:
            break

        page += 1

    print(f"[EXTRACT] total orders: {len(orders)}")

    return orders