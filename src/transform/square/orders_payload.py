from decimal import Decimal, InvalidOperation

import pandas as pd


def to_decimal(value, label):
    """값을 Decimal로 변환하고 유효한 숫자인지 확인한다."""
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{label} 값이 올바르지 않습니다: {value}") from None

    if not number.is_finite():
        raise ValueError(f"{label} 값이 올바르지 않습니다: {value}")

    return number


def to_cents(value):
    """CAD 금액을 센트 정수로 변환한다. 예: 7.25 → 725."""
    amount = to_decimal(value, "금액") * 100

    if amount < 0 or amount != amount.to_integral_value():
        raise ValueError(f"올바르지 않은 금액입니다: {value}")

    return int(amount)


def require_square_id(value, label):
    """Square ID가 비어 있거나 예시 문자열이면 중단한다."""
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
    """
    매장 주문 한 건과 주문 항목을 Square 요청 payload로 변환한다.

    현재 지원 범위:
    - RETAIL 주문
    - 원본 상태가 COMPLETED인 주문
    - 할인과 배송비가 없는 주문
    - 정수 수량의 상품

    API 호출과 CSV 저장은 이 함수에서 하지 않는다.
    """

    # 1. 주문과 주문 항목 확인
    if len(order_df) != 1:
        raise ValueError("주문은 정확히 한 건만 전달해주세요.")

    if items_df.empty:
        raise ValueError("주문 항목이 없습니다.")

    order = order_df.iloc[0]

    if order["channel"] != "RETAIL":
        raise ValueError("매장 주문만 Square로 전송합니다.")

    if order["order_status"] != "COMPLETED":
        raise ValueError("취소·환불 주문은 별도 처리가 필요합니다.")

    if not items_df["order_id"].eq(order["order_id"]).all():
        raise ValueError("다른 주문의 상품 항목이 포함되어 있습니다.")

    if not items_df["store_id"].eq(order["store_id"]).all():
        raise ValueError("주문과 주문 항목의 매장이 일치하지 않습니다.")

    item_ids = items_df["id"].astype("string").str.strip()

    if item_ids.isna().any() or item_ids.eq("").any():
        raise ValueError("주문 항목 ID가 비어 있습니다.")

    if item_ids.duplicated().any():
        raise ValueError("주문 항목 ID가 중복되어 있습니다.")

    # 현재 버전에서 처리하지 않는 금액 조건
    if (
        order["discount_type"] != "NONE"
        or to_cents(order["discount_amount"]) != 0
        or to_cents(order["shipping_amount"]) != 0
        or any(
            to_cents(value) != 0
            for value in items_df["discount_amount"]
        )
    ):
        raise ValueError("할인·배송비 처리는 아직 구현하지 않았습니다.")

    # 2. 요청 식별값과 Square 매장 ID 확인
    if not isinstance(idempotency_key, str) or not idempotency_key.strip():
        raise ValueError("idempotency_key가 필요합니다.")

    square_location_id = require_square_id(
        square_location_id,
        "Square Location ID",
    )

    # 3. 주문 항목 변환
    line_items = []
    subtotal_cents = 0

    for _, item in items_df.iterrows():
        sku = str(item["sku"]).strip()

        # SKU로 기존 Square 상품의 Variation ID를 찾는다.
        variation_id = require_square_id(
            variation_ids_by_sku.get(sku),
            f"{sku}의 Square Variation ID",
        )

        quantity = to_decimal(item["quantity"], f"{sku} 수량")

        if quantity <= 0 or quantity != quantity.to_integral_value():
            raise ValueError(f"수량은 양의 정수여야 합니다: {sku}")

        # 현재 상품 가격이 아닌 주문 당시 단가 사용
        unit_price_cents = to_cents(item["unit_price"])
        line_total_cents = unit_price_cents * int(quantity)

        if line_total_cents != to_cents(item["line_total"]):
            raise ValueError(
                f"수량 × 단가와 주문 항목 금액이 다릅니다: {sku}"
            )

        subtotal_cents += line_total_cents

        line_items.append(
            {
                "uid": str(item["id"]).strip(),
                "catalog_object_id": variation_id,
                "quantity": str(int(quantity)),
                "base_price_money": {
                    "amount": unit_price_cents,
                    "currency": "CAD",
                },
            }
        )

    # 4. 원본 금액 검증
    if subtotal_cents != to_cents(order["subtotal"]):
        raise ValueError("주문 소계와 상품 항목 합계가 일치하지 않습니다.")

    tax_amount_cents = to_cents(order["tax_amount"])
    expected_total_cents = subtotal_cents + tax_amount_cents

    if expected_total_cents != to_cents(order["total_amount"]):
        raise ValueError("원본 주문 총액이 일치하지 않습니다.")

    tax_rate = to_decimal(order["tax_rate"], "세율")

    if tax_rate < 0:
        raise ValueError("세율은 음수일 수 없습니다.")

    if tax_rate == 0 and tax_amount_cents != 0:
        raise ValueError("세율은 0인데 원본 세금 금액이 존재합니다.")

    # 5. Square 주문 구성
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

    # 6. 원본에 고객이 있으면 Square 고객 연결
    customer_id = order["customer_id"]

    if pd.notna(customer_id) and str(customer_id).strip():
        square_order["customer_id"] = require_square_id(
            square_customer_id,
            "Square Customer ID",
        )

    # 7. 세금 규칙 추가
    if tax_rate > 0:
        square_order["taxes"] = [
            {
                "uid": "source-order-tax",
                "name": "Sales Tax",
                "type": "ADDITIVE",
                "scope": "ORDER",
                # 0.0500 → "5"
                "percentage": format(
                    (tax_rate * 100).normalize(),
                    "f",
                ),
            }
        ]

    # 8. 최종 요청 payload 반환
    return {
        "idempotency_key": idempotency_key,
        "order": square_order,
    }