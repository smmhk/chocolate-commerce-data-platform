from datetime import datetime, timezone

import pandas as pd

from src.config.paths import RAW_DATA_DIR
from src.extract.load_csv import load_csv

import json

from src.config.paths import PROCESSED_DATA_DIR
from src.square.orders import create_order
from src.transform.orders import transform_order, to_cents


pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
pd.set_option("display.max_colwidth", None)
pd.set_option("display.width", None)


orders_path = RAW_DATA_DIR / "orders_export.csv"
order_items_path = RAW_DATA_DIR / "order_items_export.csv"

orders_df = load_csv(orders_path)
order_items_df = load_csv(order_items_path)


# 매장 주문만 가져오기
retail_orders_df = orders_df.loc[
    orders_df["channel"] == "RETAIL"
].copy()

print("RETAIL ORDERS DF : ", retail_orders_df)


# 첫 테스트는 완료된 매장 주문 중 한 건 선택
completed_orders_df = retail_orders_df.loc[
    retail_orders_df["order_status"] == "COMPLETED"
]

if completed_orders_df.empty:
    raise ValueError("테스트할 완료된 매장 주문이 없습니다.")

# 상품 테스트와 동일하게 DataFrame 형태 유지
order_df = completed_orders_df.iloc[[0]].copy()

print("TEST TARGET ORDER DF : ", order_df)


# 선택한 주문 번호 가져오기
# target_order_id = order_df["order_id"].iloc[0]

# 테스트할 주문 한 건을 DataFrame으로 가져오기
target_order_id = "CCF-000004"
print("targeted order_id >>>>", target_order_id)


# 해당 주문에 속한 상품 항목 가져오기
# order_items.order_id와 orders.order_id를 연결한다.
items_df = order_items_df.loc[
    order_items_df["order_id"] == target_order_id
].copy()

if items_df.empty:
    raise ValueError(f"주문 항목이 없습니다: {target_order_id}")

print("TEST TARGET ORDER ITEMS DF : ", items_df)

# BUR001 매장에 해당하는 Square Location ID
square_location_id = "<BUR001의 Square Location ID>"

# 선택한 주문의 customer_id에 해당하는 Square Customer ID
square_customer_id = "<해당 고객의 Square Customer ID>"

# SKU에 해당하는 Square Item Variation ID
variation_ids_by_sku = {
    "CCF-BAR-002": "<CCF-BAR-002의 Square Variation ID>",
}


# 동일한 테스트 요청을 재실행할 때 같은 키를 사용한다.
idempotency_key = f"ccf-sandbox-order-{target_order_id}-v1"

payload = transform_order(
    order_df=order_df,
    items_df=items_df,
    square_location_id=square_location_id,
    square_customer_id=square_customer_id,
    variation_ids_by_sku=variation_ids_by_sku,
    idempotency_key=idempotency_key,
)

print("\n=== Square Order Payload ===")
print(json.dumps(payload, indent=2, ensure_ascii=False))


# 재시도 시 요청 내용이 바뀌지 않았는지 확인한다.
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

request_path = (
    PROCESSED_DATA_DIR / f"{target_order_id}_request.json"
)

if request_path.exists():
    saved_payload = json.loads(
        request_path.read_text(encoding="utf-8")
    )

    if saved_payload != payload:
        raise ValueError(
            "이전에 저장한 요청과 내용이 다릅니다. "
            "기존 주문 생성 여부를 확인한 후 변경해주세요."
        )
else:
    request_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# Square 주문 생성
square_order = create_order(payload)

print("\n=== Square Order Result ===")
print(json.dumps(square_order, indent=2, ensure_ascii=False))
print("square_order_id >>>>", square_order["id"])


# 생성 결과를 먼저 보관한다.
response_path = (
    PROCESSED_DATA_DIR / f"{target_order_id}_response.json"
)

response_path.write_text(
    json.dumps(square_order, indent=2, ensure_ascii=False),
    encoding="utf-8",
)


# Square 계산 금액과 원본 금액 비교
expected_tax = to_cents(order_df["tax_amount"].iloc[0])
expected_total = to_cents(order_df["total_amount"].iloc[0])

actual_tax = square_order["total_tax_money"]["amount"]
actual_total = square_order["total_money"]["amount"]

print("\n=== 금액 비교: 센트 기준 ===")
print(f"세금: 원본 {expected_tax} / Square {actual_tax}")
print(f"총액: 원본 {expected_total} / Square {actual_total}")

if actual_tax != expected_tax or actual_total != expected_total:
    raise ValueError(
        f"주문은 생성되었지만 금액이 다릅니다. "
        f"Square Order ID: {square_order['id']}. "
        "세금 계산과 반올림 방식을 확인해주세요."
    )

print("\nSquare 주문 생성 및 금액 검증 완료!")


# 저장할 CSV를 문자열로 다시 읽는다.
# 전화번호, ID, 빈 값 등 원본 표현을 유지한다.
orders_save_df = pd.read_csv(
    orders_path,
    sep=";",
    dtype=str,
    keep_default_na=False,
)

items_save_df = pd.read_csv(
    order_items_path,
    sep=";",
    dtype=str,
    keep_default_na=False,
)


# 1. 저장 대상 주문 확인
order_mask = orders_save_df["order_id"].eq(target_order_id)

if order_mask.sum() != 1:
    raise ValueError(
        f"저장할 주문이 정확히 한 건이어야 합니다: {target_order_id}"
    )

if square_order.get("reference_id") != target_order_id:
    raise ValueError("Square 응답의 주문 번호가 저장 대상과 다릅니다.")


# 2. Square 주문 항목과 원본 항목 연결 확인
# transform_order()에서 원본 항목 id를 uid로 전송했다.
square_items_by_uid = {
    item["uid"]: item
    for item in square_order["line_items"]
}

items_mask = items_save_df["order_id"].eq(target_order_id)

source_item_ids = set(
    items_save_df.loc[items_mask, "id"]
)

if source_item_ids != set(square_items_by_uid):
    raise ValueError("원본과 Square의 주문 항목 ID가 일치하지 않습니다.")


# 3. 주문 CSV의 Square 연동 정보 업데이트
synced_at = datetime.now(timezone.utc).isoformat()

order_sync_values = {
    "square_order_id": square_order["id"],
    "square_customer_id": square_order.get("customer_id", ""),
    "square_location_id": square_order["location_id"],
    "square_sync_status": "SUCCESS",
    "square_synced_at": synced_at,
    "square_sync_error": "",
}

for column, value in order_sync_values.items():
    orders_save_df.loc[order_mask, column] = value


# 4. 주문 항목 CSV의 Square 연결 정보 업데이트
for index in items_save_df.index[items_mask]:
    source_item_id = items_save_df.at[index, "id"]
    square_item = square_items_by_uid[source_item_id]

    items_save_df.at[index, "square_line_item_uid"] = (
        square_item["uid"]
    )

    items_save_df.at[index, "square_catalog_object_id"] = (
        square_item["catalog_object_id"]
    )


# 5. 임시 파일에 먼저 쓴 뒤 원본 파일 교체
# 각 파일의 저장 도중 원본이 잘리는 위험을 줄인다.
orders_temp_path = orders_path.with_suffix(".csv.tmp")
items_temp_path = order_items_path.with_suffix(".csv.tmp")

try:
    orders_save_df.to_csv(
        orders_temp_path,
        sep=";",
        index=False,
        encoding="utf-8",
    )

    items_save_df.to_csv(
        items_temp_path,
        sep=";",
        index=False,
        encoding="utf-8",
    )

    # 항목 저장 후 주문의 SUCCESS 상태를 저장한다.
    items_temp_path.replace(order_items_path)
    orders_temp_path.replace(orders_path)

except OSError as error:
    raise RuntimeError(
        f"Square 주문은 생성됐지만 CSV 저장에 실패했습니다. "
        f"Square Order ID: {square_order['id']}. "
        "두 CSV의 저장 상태를 확인하고, "
        "보관한 응답으로 저장 작업만 다시 진행해주세요."
    ) from error


print("\n=== CSV 저장 완료 ===")
print("원본 주문 번호 >>>>", target_order_id)
print("Square 주문 ID >>>>", square_order["id"])
print("주문 CSV >>>>", orders_path)
print("주문 항목 CSV >>>>", order_items_path)