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