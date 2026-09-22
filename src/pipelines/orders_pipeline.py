import json
from datetime import datetime, timezone

import pandas as pd

from src.config.paths import RAW_DATA_DIR, PROCESSED_DATA_DIR
from src.square.orders import create_order
from src.transform.orders import transform_order, to_cents


def read_csv(path):
    """ID와 원본 값을 문자열로 유지해서 읽는다."""
    return pd.read_csv(
        path,
        sep=";",
        dtype=str,
        keep_default_na=False,
    )


def find_square_id(df, key_column, key_value, id_column):
    """원본 식별값에 해당하는 Square ID 한 개를 가져온다."""
    matched_df = df.loc[df[key_column] == key_value]

    if len(matched_df) != 1:
        raise ValueError(
            f"{key_column}={key_value}: "
            f"연결 대상이 정확히 한 건이어야 합니다."
        )

    square_id = matched_df[id_column].iloc[0].strip()

    if not square_id:
        raise ValueError(
            f"{key_column}={key_value}: {id_column}가 비어 있습니다."
        )

    return square_id


def save_csv(df, path):
    """임시 파일에 쓴 뒤 원본을 교체한다."""
    temp_path = path.with_suffix(".csv.tmp")

    df.to_csv(
        temp_path,
        sep=";",
        index=False,
        encoding="utf-8",
    )

    temp_path.replace(path)


def run_order_pipeline():
    # 1. 원본 CSV 읽기
    orders_path = RAW_DATA_DIR / "orders_export.csv"
    items_path = RAW_DATA_DIR / "order_items_export.csv"

    orders_df = read_csv(orders_path)
    order_items_df = read_csv(items_path)
    stores_df = read_csv(RAW_DATA_DIR / "stores_export.csv")
    customers_df = read_csv(RAW_DATA_DIR / "customers_export.csv")
    products_df = read_csv(RAW_DATA_DIR / "products_export.csv")

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if orders_df["order_id"].duplicated().any():
        raise ValueError("원본 주문 번호가 중복되어 있습니다.")

    # 2. 완료된 매장 주문만 선택
    target_orders_df = orders_df.loc[
        (orders_df["channel"] == "RETAIL")
        & (orders_df["order_status"] == "COMPLETED")
    ].copy()

    print(f"처리 대상: {len(target_orders_df)}건")

    success_count = 0
    skip_count = 0

    # 3. 주문 한 건씩 반복
    for index in target_orders_df.index:
        order_df = orders_df.loc[[index]].copy()
        order = order_df.iloc[0]
        target_order_id = order["order_id"]

        print(f"\n=== 주문 처리: {target_order_id} ===")

        # 저장까지 완료된 주문은 건너뛴다.
        if (
            order["square_sync_status"] == "SUCCESS"
            and order["square_order_id"].strip()
        ):
            print("이미 연동한 주문입니다. 건너뜁니다.")
            skip_count += 1
            continue

        try:
            # 4. 해당 주문의 항목 선택
            items_df = order_items_df.loc[
                order_items_df["order_id"] == target_order_id
            ].copy()

            # 5. 매장 Square ID 조회
            square_location_id = find_square_id(
                stores_df,
                "store_id",
                order["store_id"],
                "square_location_id",
            )

            # 6. 고객 Square ID 조회
            # 비회원이면 고객 연결 없이 진행한다.
            square_customer_id = None

            if order["customer_id"].strip():
                square_customer_id = find_square_id(
                    customers_df,
                    "id",
                    order["customer_id"],
                    "square_customer_id",
                )

            # 7. 주문에 포함된 상품의 Variation ID 조회
            variation_ids_by_sku = {}

            for sku in items_df["sku"].unique():
                variation_ids_by_sku[sku] = find_square_id(
                    products_df,
                    "sku",
                    sku,
                    "square_catalog_object_id",
                )

            # 단건 테스트와 같은 키 규칙을 사용한다.
            idempotency_key = (
                f"ccf-sandbox-order-{target_order_id}-v1"
            )

            # 8. 요청 payload 변환
            payload = transform_order(
                order_df=order_df,
                items_df=items_df,
                square_location_id=square_location_id,
                square_customer_id=square_customer_id,
                variation_ids_by_sku=variation_ids_by_sku,
                idempotency_key=idempotency_key,
            )

            request_path = (
                PROCESSED_DATA_DIR
                / f"{target_order_id}_request.json"
            )
            response_path = (
                PROCESSED_DATA_DIR
                / f"{target_order_id}_response.json"
            )

            # 응답만 있고 원래 요청이 없으면 자동 처리하지 않는다.
            if response_path.exists() and not request_path.exists():
                raise ValueError(
                    "응답 파일은 있지만 요청 파일이 없습니다. "
                    "기존 요청을 확인해주세요."
                )

            # 9. 기존 요청과 같은 내용인지 확인
            if request_path.exists():
                saved_payload = json.loads(
                    request_path.read_text(encoding="utf-8")
                )

                if saved_payload != payload:
                    raise ValueError(
                        "이전에 저장한 요청과 내용이 다릅니다. "
                        "기존 Square 주문을 먼저 확인해주세요."
                    )
            else:
                request_path.write_text(
                    json.dumps(
                        payload,
                        indent=2,
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )

            # 10. 보관한 생성 응답이 있으면 저장 작업부터 복구
            if response_path.exists():
                square_order = json.loads(
                    response_path.read_text(encoding="utf-8")
                )
                print("기존 생성 응답으로 검증·저장을 재시도합니다.")

            else:
                square_order = create_order(payload)

                print(
                    "생성된 Square Order ID:",
                    square_order["id"],
                )

                response_path.write_text(
                    json.dumps(
                        square_order,
                        indent=2,
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )

            # 11. 응답의 주문·매장 연결 확인
            if (
                square_order["reference_id"] != target_order_id
                or square_order["location_id"] != square_location_id
            ):
                raise ValueError("응답의 주문 또는 매장이 다릅니다.")

            # # 12. 원본과 Square 금액 비교
            # expected_tax = to_cents(order["tax_amount"])
            # expected_total = to_cents(order["total_amount"])
            #
            # actual_tax = square_order["total_tax_money"]
            # actual_total = square_order["total_money"]
            #
            # if (
            #     actual_tax["currency"] != "CAD"
            #     or actual_total["currency"] != "CAD"
            #     or actual_tax["amount"] != expected_tax
            #     or actual_total["amount"] != expected_total
            # ):
            #     raise ValueError(
            #         f"금액 불일치 — "
            #         f"세금: 원본 {expected_tax}, "
            #         f"Square {actual_tax['amount']} / "
            #         f"총액: 원본 {expected_total}, "
            #         f"Square {actual_total['amount']}"
            #     )

            # 13. 주문 항목 연결 확인
            square_items_by_uid = {
                item["uid"]: item
                for item in square_order["line_items"]
            }

            if set(items_df["id"]) != set(square_items_by_uid):
                raise ValueError("원본과 Square의 항목 ID가 다릅니다.")

            # 14. 주문 항목의 Square 정보 기록
            for item_index in items_df.index:
                item_id = order_items_df.at[item_index, "id"]
                square_item = square_items_by_uid[item_id]

                order_items_df.at[
                    item_index, "square_line_item_uid"
                ] = square_item["uid"]

                order_items_df.at[
                    item_index, "square_catalog_object_id"
                ] = square_item["catalog_object_id"]

            # 15. 주문의 Square 정보 기록
            sync_values = {
                "square_order_id": square_order["id"],
                "square_customer_id": square_order.get(
                    "customer_id", ""
                ),
                "square_location_id": square_order["location_id"],
                "square_sync_status": "SUCCESS",
                "square_synced_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "square_sync_error": "",
            }

            for column, value in sync_values.items():
                orders_df.at[index, column] = value

            # 16. 항목 CSV부터 저장하고 주문 CSV 저장
            save_csv(order_items_df, items_path)
            save_csv(orders_df, orders_path)

            success_count += 1
            print(f"연동 및 저장 완료: {target_order_id}")

        except Exception as error:
            print(f"처리 중단: {target_order_id}")
            print(f"오류: {error}")
            print(
                "Square에 이미 생성됐을 수 있습니다. "
                "보관한 요청·응답을 확인해주세요."
            )
            raise

    print("\n=== 주문 파이프라인 완료 ===")
    print(f"이번 실행 저장 완료: {success_count}건")
    print(f"기존 성공 주문 건너뜀: {skip_count}건")


if __name__ == "__main__":
    run_order_pipeline()