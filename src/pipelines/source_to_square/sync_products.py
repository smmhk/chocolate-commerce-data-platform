import hashlib
import json
import logging
import shutil
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pandas as pd
import requests

from src.clients.square.config import headers
from src.config.paths import get_online_source_dir


LOGGER = logging.getLogger(__name__)
BASE_URL = "https://connect.squareupsandbox.com/v2"


def call_square(endpoint, payload):
    response = requests.post(
        f"{BASE_URL}/{endpoint}",
        headers=headers,
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    if data.get("errors"):
        raise RuntimeError(f"Square API 오류: {data['errors']}")

    return data


def find_variation(sku):
    """검색 결과 중 SKU가 정확히 일치하는 Variation만 선택한다."""
    matches = {}
    cursor = None
    seen_cursors = set()

    while True:
        payload = {"text_filter": sku}
        if cursor:
            payload["cursor"] = cursor

        data = call_square("catalog/search-catalog-items", payload)

        for item in data.get("items", []):
            if item.get("is_deleted"):
                continue

            for variation in item.get("item_data", {}).get("variations", []):
                if variation.get("is_deleted"):
                    continue

                variation_sku = variation.get(
                    "item_variation_data", {}
                ).get("sku")

                if variation_sku == sku:
                    matches[variation["id"]] = variation

        cursor = data.get("cursor")
        if not cursor:
            break
        if cursor in seen_cursors:
            raise RuntimeError("Square 검색 cursor가 반복됩니다.")
        seen_cursors.add(cursor)

    if len(matches) > 1:
        raise ValueError(f"Square에 같은 SKU의 Variation이 여러 개입니다: {sku}")

    return next(iter(matches.values()), None)


def create_variation(row):
    price = Decimal(row["price"])

    if not price.is_finite() or price < 0:
        raise ValueError(f"잘못된 상품 가격: {row['sku']}")

    cents = price * 100
    if cents != cents.to_integral_value():
        raise ValueError(f"가격은 소수점 둘째 자리까지만 가능합니다: {row['sku']}")

    catalog_object = {
        "type": "ITEM",
        "id": "#item",
        "item_data": {
            "name": row["product_name"],
            "description": row.get("description", ""),
            "variations": [
                {
                    "type": "ITEM_VARIATION",
                    "id": "#variation",
                    "item_variation_data": {
                        "item_id": "#item",
                        "name": "Regular",
                        "sku": row["sku"],
                        "pricing_type": "FIXED_PRICING",
                        "price_money": {
                            "amount": int(cents),
                            "currency": "CAD",
                        },
                    },
                }
            ],
        },
    }

    # 동일 요청을 재시도할 때 같은 키 사용
    fingerprint = hashlib.sha256(
        json.dumps(
            catalog_object,
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()

    data = call_square(
        "catalog/object",
        {
            "idempotency_key": fingerprint,
            "object": catalog_object,
        },
    )

    variations = data["catalog_object"]["item_data"]["variations"]
    matches = [
        variation
        for variation in variations
        if variation.get("item_variation_data", {}).get("sku") == row["sku"]
    ]

    if len(matches) != 1 or not matches[0].get("id"):
        raise ValueError(f"생성 응답의 Variation을 확인할 수 없습니다: {row['sku']}")

    return matches[0]


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


def run_products_pipeline():
    products_path = get_online_source_dir() / "products_export.csv"

    products_df = pd.read_csv(
        products_path,
        sep=";",
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
    )

    required = {"sku", "product_name", "price"}
    missing = required - set(products_df.columns)
    if missing:
        raise ValueError(f"필수 컬럼이 없습니다: {missing}")

    skus = products_df["sku"]

    if skus.str.strip().eq("").any():
        raise ValueError("빈 SKU가 있습니다.")
    if skus.ne(skus.str.strip()).any():
        raise ValueError("SKU 앞뒤 공백을 제거해주세요.")
    if skus.duplicated().any():
        raise ValueError("원본 CSV에 중복 SKU가 있습니다.")

    for column in (
        "square_catalog_object_id",
        "square_sync_status",
        "square_synced_at",
        "square_sync_error",
    ):
        if column not in products_df.columns:
            products_df[column] = ""

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup_path = products_path.with_name(
        f"{products_path.name}.{timestamp}.bak"
    )
    shutil.copy2(products_path, backup_path)

    LOGGER.info("stage=extract source=%s rows=%d", products_path, len(products_df))
    LOGGER.info("stage=backup path=%s", backup_path)

    existing_count = 0
    created_count = 0

    for index, row in products_df.iterrows():
        sku = row["sku"]

        try:
            variation = find_variation(sku)

            if variation is not None:
                existing_count += 1
                LOGGER.info("stage=search sku=%s status=exists", sku)
            else:
                variation = create_variation(row)
                created_count += 1
                LOGGER.info("stage=create sku=%s status=completed", sku)

            variation_id = variation["id"]
            LOGGER.info(
                "stage=mapping sku=%s variation_id=%s",
                sku,
                variation_id,
            )

            products_df.at[index, "square_catalog_object_id"] = variation_id
            products_df.at[index, "square_sync_status"] = "SUCCESS"
            products_df.at[index, "square_synced_at"] = (
                datetime.now(timezone.utc).isoformat()
            )
            products_df.at[index, "square_sync_error"] = ""

            save_csv(products_df, products_path)
            LOGGER.info("stage=save_csv sku=%s status=completed", sku)

        except Exception:
            LOGGER.exception("status=failed sku=%s", sku)
            raise

    LOGGER.info(
        "status=completed total=%d existing=%d created=%d",
        len(products_df),
        existing_count,
        created_count,
    )


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
        force=True,
    )
    run_products_pipeline()