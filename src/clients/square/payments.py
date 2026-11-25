"""Square Sandbox payment operations for completing imported POS orders."""

from src.clients.square.orders import sandbox_request


def list_order_payments(order):
    """Read every payment page for the location and keep this order's records."""
    params = {
        "location_id": order["location_id"],
        "begin_time": order["created_at"],
    }
    payments = []
    seen_cursors = set()

    while True:
        result = sandbox_request("GET", "/payments", params=params)
        payments.extend(
            payment for payment in result.get("payments", [])
            if payment.get("order_id") == order["id"]
        )
        cursor = result.get("cursor")
        if not cursor:
            return payments
        if cursor in seen_cursors:
            raise RuntimeError("Square 결제 조회 커서가 반복됩니다.")
        seen_cursors.add(cursor)
        params["cursor"] = cursor


def approve_external_payment(order, idempotency_key):
    result = sandbox_request(
        "POST",
        "/payments",
        json={
            "source_id": "EXTERNAL",
            "idempotency_key": idempotency_key,
            "order_id": order["id"],
            "location_id": order["location_id"],
            "amount_money": order["total_money"],
            "autocomplete": False,
            "external_details": {
                "type": "OTHER",
                "source": "Lovable POS simulated cash",
            },
        },
    )
    return result["payment"]
