import json
import logging
import shutil
import sys
from datetime import datetime, timezone

import pandas as pd

from src.clients.square.orders import create_order, retrieve_order
from src.config.paths import get_online_source_dir, PROCESSED_DATA_DIR
from src.pipelines.source_to_square.complete_order import complete_cash_order
from src.transform.square.orders_payload import transform_order, to_cents


LOGGER = logging.getLogger(__name__)


def read_csv(path):
    return pd.read_csv(
        path,
        sep=";",
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
    )


def save_csv(df, path):
    temporary_path = path.with_suffix(".csv.tmp")
    try:
        df.to_csv(
            temporary_path,
            sep=";",
            index=False,
            encoding="utf-8-sig",
        )
        temporary_path.replace(path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def find_square_id(df, key_column, key_value, id_column):
    matches = df.loc[df[key_column].eq(key_value)]

    if len(matches) != 1:
        raise ValueError(
            f"{key_column}={key_value}: 연결 대상이 정확히 한 건이어야 합니다."
        )

    square_id = matches[id_column].iloc[0].strip()

    if not square_id or square_id.startswith("<"):
        raise ValueError(
            f"{key_column}={key_value}: {id_column}가 없거나 올바르지 않습니다."
        )

    return square_id


def run_order_pipeline():
    source_dir = get_online_source_dir()
    orders_path = source_dir / "orders_export.csv"
    items_path = source_dir / "order_items_export.csv"

    orders = read_csv(orders_path)
    items = read_csv(items_path)
    stores = read_csv(source_dir / "stores_export.csv")
    customers = read_csv(source_dir / "customers_export.csv")
    products = read_csv(source_dir / "products_export.csv")

    if orders["order_id"].str.strip().eq("").any():
        raise ValueError("빈 주문 번호가 있습니다.")
    if orders["order_id"].duplicated().any():
        raise ValueError("주문 번호가 중복되어 있습니다.")
    if items["id"].str.strip().eq("").any():
        raise ValueError("빈 주문항목 ID가 있습니다.")
    if items["id"].duplicated().any():
        raise ValueError("주문항목 ID가 중복되어 있습니다.")

    target = orders.loc[
        orders["channel"].eq("RETAIL")
        & orders["order_status"].eq("COMPLETED")
    ]

    # 기존 실행에서 보관한 요청·응답도 계속 사용
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    LOGGER.info(
        "status=started source=%s target_orders=%d",
        source_dir,
        len(target),
    )

    jobs = []
    skipped = 0
    errors = []

    # 모든 대상의 ID·금액·지원 조건을 API 전송 전에 검사
    for index, order in target.iterrows():
        order_id = order["order_id"]

        existing_order_id = order.get("square_order_id", "").strip()
        is_cash_order = order.get("payment_method", "").strip().upper() == "CASH"
        if (
            not is_cash_order
            and order.get("square_sync_status") == "SUCCESS"
            and existing_order_id
        ):
            skipped += 1
            LOGGER.info("stage=select order_id=%s status=skipped", order_id)
            continue

        try:
            order_items = items.loc[items["order_id"].eq(order_id)].copy()

            location_id = find_square_id(
                stores, "store_id", order["store_id"], "square_location_id"
            )

            customer_id = None
            if order["customer_id"].strip():
                customer_id = find_square_id(
                    customers,
                    "id",
                    order["customer_id"],
                    "square_customer_id",
                )

            variation_ids = {
                sku: find_square_id(
                    products, "sku", sku, "square_catalog_object_id"
                )
                for sku in order_items["sku"].unique()
            }

            payload = transform_order(
                order_df=orders.loc[[index]].copy(),
                items_df=order_items,
                square_location_id=location_id,
                square_customer_id=customer_id,
                variation_ids_by_sku=variation_ids,
                idempotency_key=f"ccf-sandbox-order-{order_id}-v1",
            )

            # ファイル名には注文番号そのものではなくハッシュを使う必要が
            # ない既存の命名規則を維持。ただしパス文字は拒否する。
            if any(char in order_id for char in ("/", "\\", "\0")):
                raise ValueError("注文番号にファイルパス文字が含まれています。")

            request_path = PROCESSED_DATA_DIR / f"{order_id}_request.json"
            response_path = PROCESSED_DATA_DIR / f"{order_id}_response.json"

            if not existing_order_id and response_path.exists() and not request_path.exists():
                raise ValueError("応答ファイルはありますが、元のリクエストがありません。")

            if not existing_order_id and request_path.exists():
                saved_payload = json.loads(
                    request_path.read_text(encoding="utf-8")
                )
                if saved_payload != payload:
                    raise ValueError(
                        "기존 요청과 내용이 다릅니다. 기존 Square 주문 확인이 필요합니다."
                    )

            jobs.append(
                (
                    index, order_items, payload, request_path, response_path,
                    existing_order_id, is_cash_order,
                )
            )

        except Exception as error:
            errors.append((order_id, str(error)))
            LOGGER.error(
                "stage=preflight order_id=%s status=failed reason=%s",
                order_id,
                error,
            )

    if errors:
        raise ValueError(
            f"사전 검증 실패: {len(errors)}건. 이번 실행에서는 주문을 전송하지 않았습니다."
        )

    LOGGER.info(
        "stage=preflight status=completed pending=%d skipped=%d",
        len(jobs),
        skipped,
    )

    completed = 0
    backed_up = False

    for (
        index, order_items, payload, request_path, response_path,
        existing_order_id, is_cash_order,
    ) in jobs:
        order_id = orders.at[index, "order_id"]

        try:
            if existing_order_id:
                square_order = retrieve_order(existing_order_id)
            elif response_path.exists():
                saved_order = json.loads(response_path.read_text(encoding="utf-8"))
                square_order = (
                    retrieve_order(saved_order["id"]) if is_cash_order else saved_order
                )
                LOGGER.info("stage=response order_id=%s status=recovered", order_id)
            else:
                if not request_path.exists():
                    request_path.write_text(
                        json.dumps(payload, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                created_order = create_order(payload)
                response_path.write_text(
                    json.dumps(created_order, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                square_order = (
                    retrieve_order(created_order["id"]) if is_cash_order else created_order
                )
                LOGGER.info(
                    "stage=create order_id=%s square_order_id=%s status=completed",
                    order_id,
                    square_order["id"],
                )

            if (
                square_order["reference_id"] != order_id
                or square_order["location_id"] != payload["order"]["location_id"]
                or square_order.get("customer_id")
                != payload["order"].get("customer_id")
            ):
                raise ValueError("응답의 주문·매장·고객 연결이 다릅니다.")

            # 세금과 총액 모두 ±1센트까지 허용
            tolerance_cents = 1

            for source_column, square_column in (
                    ("tax_amount", "total_tax_money"),
                    ("total_amount", "total_money"),
            ):
                money = square_order[square_column]
                expected = to_cents(orders.at[index, source_column])
                actual = money["amount"]
                difference = actual - expected

                LOGGER.info(
                    "stage=validate_money order_id=%s field=%s "
                    "expected_cents=%d actual_cents=%d difference_cents=%d currency=%s",
                    order_id,
                    source_column,
                    expected,
                    actual,
                    difference,
                    money["currency"],
                )

                if money["currency"] != "CAD":
                    raise ValueError(
                        f"통화 불일치: {source_column}, {money['currency']}"
                    )

                if abs(difference) > tolerance_cents:
                    raise ValueError(
                        f"허용 범위 초과: {source_column}, "
                        f"원본={expected}센트, Square={actual}센트, "
                        f"차이={difference}센트"
                    )

                if difference != 0:
                    LOGGER.warning(
                        "stage=validate_money order_id=%s field=%s "
                        "status=accepted_with_tolerance difference_cents=%d tolerance_cents=%d",
                        order_id,
                        source_column,
                        difference,
                        tolerance_cents,
                    )

            square_items = square_order.get("line_items", [])
            by_uid = {item["uid"]: item for item in square_items}

            if (
                len(by_uid) != len(square_items)
                or set(order_items["id"]) != set(by_uid)
            ):
                raise ValueError("원본과 Square의 주문항목 ID가 다릅니다.")

            requested_items = {
                line["uid"]: line for line in payload["order"]["line_items"]
            }
            mappings_match = True
            checked_fields = ("catalog_object_id",)
            if is_cash_order:
                checked_fields += ("quantity", "base_price_money")

            for item_index, item in order_items.iterrows():
                square_item = by_uid[item["id"]]
                requested_item = requested_items[item["id"]]
                for field in checked_fields:
                    if square_item.get(field) != requested_item[field]:
                        raise ValueError("응답의 상품 Variation ID, 수량 또는 단가가 다릅니다.")

                square_uid = square_item["uid"]
                variation_id = square_item["catalog_object_id"]
                if (
                    item.get("square_line_item_uid") != square_uid
                    or item.get("square_catalog_object_id") != variation_id
                ):
                    mappings_match = False
                    items.at[item_index, "square_line_item_uid"] = square_uid
                    items.at[item_index, "square_catalog_object_id"] = variation_id

            if is_cash_order:
                prior_state = square_order["state"]
                complete_cash_order(square_order)
                LOGGER.info("stage=order_completion order_id=%s state=COMPLETED", order_id)
                if (
                    prior_state == "COMPLETED"
                    and existing_order_id
                    and orders.loc[index].get("square_sync_status") == "SUCCESS"
                    and orders.loc[index].get("square_location_id") == square_order["location_id"]
                    and orders.loc[index].get("square_customer_id", "") == square_order.get("customer_id", "")
                    and mappings_match
                ):
                    skipped += 1
                    continue

            if not backed_up:
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
                for path in (orders_path, items_path):
                    backup = path.with_name(f"{path.name}.{timestamp}.bak")
                    shutil.copy2(path, backup)
                    LOGGER.info("stage=backup path=%s", backup)
                backed_up = True

            values = {
                "square_order_id": square_order["id"],
                "square_customer_id": square_order.get("customer_id", ""),
                "square_location_id": square_order["location_id"],
                "square_sync_status": "SUCCESS",
                "square_synced_at": datetime.now(timezone.utc).isoformat(),
                "square_sync_error": "",
            }
            for column, value in values.items():
                orders.at[index, column] = value

            # 항목 먼저 저장하고 주문 성공 상태 저장
            save_csv(items, items_path)
            save_csv(orders, orders_path)
            completed += 1

            LOGGER.info(
                "stage=save_csv order_id=%s items=%d status=completed",
                order_id,
                len(order_items),
            )

        except Exception:
            LOGGER.exception("status=failed order_id=%s", order_id)
            raise

    LOGGER.info(
        "status=completed target=%d saved=%d skipped=%d",
        len(target),
        completed,
        skipped,
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
        force=True,
    )
    run_order_pipeline()