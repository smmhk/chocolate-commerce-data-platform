"""Complete one verified Lovable cash order in Square Sandbox."""

from hashlib import sha256

from src.clients.square.orders import pay_order, retrieve_order
from src.clients.square.payments import approve_external_payment, list_order_payments


def payment_key(operation, order_id):
    key = f"ccf-{operation}-{order_id}-v1"
    if len(key) <= 45:
        return key
    order_digest = sha256(order_id.encode("utf-8")).hexdigest()[:30]
    return f"ccf-{operation}-{order_digest}-v1"


def require_completed_order(order):
    if (
        order["state"] != "COMPLETED"
        or order.get("net_amount_due_money") != {"amount": 0, "currency": "CAD"}
    ):
        raise RuntimeError("Square 주문 완료 상태와 잔액을 확인할 수 없습니다.")


def complete_cash_order(order):
    if order["state"] == "COMPLETED":
        require_completed_order(order)
        return

    if order["state"] != "OPEN" or order.get("fulfillments"):
        raise ValueError("Fulfillment가 없는 OPEN 주문만 완료 처리할 수 있습니다.")

    total = order["total_money"]
    if (
        total["currency"] != "CAD"
        or total["amount"] <= 0
        or order.get("net_amount_due_money") != total
        or order.get("tenders")
    ):
        raise ValueError("주문에 기존 수납이 있거나 미결제 CAD 잔액이 총액과 다릅니다.")

    order_id = order["id"]
    payments = list_order_payments(order)
    if len(payments) > 1:
        raise ValueError("기존 결제가 여러 건입니다. Square에서 먼저 확인해주세요.")

    if payments:
        payment = payments[0]
    else:
        payment = approve_external_payment(order, payment_key("ext", order_id))

    if (
        payment.get("status") != "APPROVED"
        or payment.get("source_type") != "EXTERNAL"
        or payment.get("external_details", {}).get("source") != "Lovable POS simulated cash"
        or payment.get("order_id") != order_id
        or payment.get("location_id") != order["location_id"]
        or payment.get("amount_money") != total
        or payment.get("total_money") != total
        or not payment.get("id")
    ):
        raise ValueError("기존 외부 결제의 상태 또는 주문·금액 연결을 확인해주세요.")

    pay_order(order_id, payment["id"], payment_key("pay", order_id))
    completed_order = retrieve_order(order_id)
    require_completed_order(completed_order)

    unchanged_fields = (
        "reference_id", "location_id", "customer_id", "total_money",
        "total_tax_money", "line_items",
    )
    if any(completed_order.get(field) != order.get(field) for field in unchanged_fields):
        raise ValueError("완료 전후 Square 주문 금액 또는 매핑이 변경되었습니다.")
