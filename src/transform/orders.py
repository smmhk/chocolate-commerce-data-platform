from decimal import Decimal

import pandas as pd


def to_cents(value):
    """CAD 금액을 센트 정수로 변환한다."""
    amount = Decimal(str(value)) * 100

    if not amount.is_finite() or amount != amount.to_integral_value():
        raise ValueError(f"올바르지 않은 금액입니다: {value}")

    return int(amount)


def require_square_id(value, label):
    """비어 있는 Square ID가 전송되지 않도록 확인한다."""
    if pd.isna(value):
        raise ValueError(f"{label}가 없습니다.")

    value = str(value).strip()

    if not value or value.startswith("<"):
        raise ValueError(f"{label}를 실제 Square ID로 입력해주세요.")

    return value


def transform_order(
    order_df,
    items_df,
    square_location_id,
    square_customer_id,
    variation_ids_by_sku,
    idempotency_key,
):
    if len(order_df) != 1:
        raise ValueError("주문은 한 건만 전달해주세요.")

    if items_df.empty:
        raise ValueError("주문 항목이 없습니다.")

    order = order_df.iloc[0]

    if order["channel"] != "RETAIL":
        raise ValueError("매장 주문만 Square로 전송합니다.")

    # 첫 테스트에서는 완료된 원본 주문만 처리한다.
    if order["order_status"] != "COMPLETED":
        raise ValueError("취소·환불 주문은 별도 처리가 필요합니다.")

    if not items_df["order_id"].eq(order["order_id"]).all():
        raise ValueError("다른 주문의 상품 항목이 포함되어 있습니다.")

    # 이번 버전은 할인·배송비가 없는 주문을 대상으로 한다.
    if (
        order["discount_type"] != "NONE"
        or to_cents(order["discount_amount"]) != 0
        or to_cents(order["shipping_amount"]) != 0
        or any(to_cents(value) != 0 for value in items_df["discount_amount"])
    ):
        raise ValueError("할인·배송비 처리는 아직 구현하지 않았습니다.")

    square_location_id = require_square_id(
        square_location_id,
        "Square Location ID",
    )

    line_items = []
    subtotal_cents = 0

    for _, item in items_df.iterrows():
        sku = str(item["sku"]).strip()

        variation_id = require_square_id(
            variation_ids_by_sku.get(sku),
            f"{sku}의 Square Variation ID",
        )

        quantity = Decimal(str(item["quantity"]))

        if (
            not quantity.is_finite()
            or quantity <= 0
            or quantity != quantity.to_integral_value()
        ):
            raise ValueError(f"올바르지 않은 상품 수량: {sku}")

        unit_price_cents = to_cents(item["unit_price"])
        line_total_cents = unit_price_cents * int(quantity)

        if line_total_cents != to_cents(item["line_total"]):
            raise ValueError(f"주문 항목 금액이 일치하지 않습니다: {sku}")

        subtotal_cents += line_total_cents

        line_items.append(
            {
                # 원본 항목 ID를 사용해 응답과 연결한다.
                "uid": str(item["id"]),
                "catalog_object_id": variation_id,
                "quantity": str(int(quantity)),
                # 현재 상품 가격 대신 주문 당시 단가를 사용한다.
                "base_price_money": {
                    "amount": unit_price_cents,
                    "currency": "CAD",
                },
            }
        )

    if subtotal_cents != to_cents(order["subtotal"]):
        raise ValueError("주문 소계와 상품 항목 합계가 일치하지 않습니다.")

    expected_total = subtotal_cents + to_cents(order["tax_amount"])

    if expected_total != to_cents(order["total_amount"]):
        raise ValueError("원본 주문 총액이 일치하지 않습니다.")

    square_order = {
        "reference_id": str(order["order_id"]),
        "location_id": square_location_id,
        "state": "OPEN",
        "line_items": line_items,
        "pricing_options": {
            "auto_apply_taxes": False,
            "auto_apply_discounts": False,
        },
    }

    # 원본에 고객이 있으면 Square 고객 ID도 반드시 연결한다.
    customer_id = order["customer_id"]

    if pd.notna(customer_id) and str(customer_id).strip():
        square_order["customer_id"] = require_square_id(
            square_customer_id,
            "Square Customer ID",
        )

    tax_rate = Decimal(str(order["tax_rate"]))

    if not tax_rate.is_finite() or tax_rate < 0:
        raise ValueError("올바르지 않은 세율입니다.")

    if tax_rate > 0:
        square_order["taxes"] = [
            {
                "uid": "source-order-tax",
                "name": "Sales Tax",
                "type": "ADDITIVE",
                "scope": "ORDER",
                # 원본 0.0500 → Square "5"
                "percentage": format(
                    (tax_rate * 100).normalize(),
                    "f",
                ),
            }
        ]

    return {
        "idempotency_key": idempotency_key,
        "order": square_order,
    }