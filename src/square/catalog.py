# Square Catalog API 통신만 담당
import json

import requests

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.square.client import headers
from src.config.paths import RAW_DATA_DIR

# Square > Catalog에 이미 등록된 SKU인지 확인
def search_product_by_sku(sku):
    search_url = "https://connect.squareupsandbox.com/v2/catalog/search-catalog-items"

    body = {
        "text_filter": sku
    }

    response = requests.post(
        search_url,
        headers=headers,
        json=body
    )

    data = response.json()

    print("call search_product_by_sku() -> response json : ", data)
    items = data.get("items", [])

    existing_product = bool(items)

    # matched_ids = data.get("matched_variation_ids", [])

    if existing_product:
        return True

    return False


"""
Request 예제

curl https://connect.squareupsandbox.com/v2/catalog/search-catalog-items \
  -X POST \
  -H 'Square-Version: 2026-08-19' \
  -H 'Authorization: Bearer [token]' \
  -H 'Content-Type: application/json' \
  -d '{
    "text_filter": "CCF-SEA-001"
  }'



response 예제
{
  "items": [
    {
      "type": "ITEM",
      "id": "FFQBNLTUFFSCW6HS73TN7KAR",
      "updated_at": "2026-09-10T06:50:16.326Z",
      "created_at": "2026-09-10T06:50:16.374Z",
      "version": 1789023016326,
      "is_deleted": false,
      "present_at_all_locations": true,
      "item_data": {
        "name": "Strawberry Chocolate Hearts",
        "description": "Strawberry cream hearts for the season.",
        "is_taxable": true,
        "variations": [
          {
            "type": "ITEM_VARIATION",
            "id": "RGVPHWDYNYGZS4NASMWWUVXX",
            "updated_at": "2026-09-10T06:50:16.326Z",
            "created_at": "2026-09-10T06:50:16.374Z",
            "version": 1789023016326,
            "is_deleted": false,
            "present_at_all_locations": true,
            "item_variation_data": {
              "item_id": "FFQBNLTUFFSCW6HS73TN7KAR",
              "name": "Regular",
              "sku": "CCF-SEA-001",
              "ordinal": 0,
              "pricing_type": "FIXED_PRICING",
              "price_money": {
                "amount": 1550,
                "currency": "CAD"
              },
              "sellable": true,
              "stockable": true
            }
          }
        ],
        "product_type": "REGULAR",
        "description_html": "<p>Strawberry cream hearts for the season.</p>",
        "description_plaintext": "Strawberry cream hearts for the season.",
        "is_archived": false
      }
    }
  ],
  "cursor": "",
  "matched_variation_ids": [
    "RGVPHWDYNYGZS4NASMWWUVXX"
  ]
}"""

# Square > 상품생성
def create_product(square_product):

    create_url = "https://connect.squareupsandbox.com/v2/catalog/object"

    # Square 상품 생성을 위한 API를 호출하고 HTTP 응답 전체를 받는다.
    # http_response에는 status code, response header, response body 등이 모두 들어 있다.
    http_response = requests.post(
        create_url,
        headers=headers,
        json=square_product
    )

    # create_response 자체를 출력하면 응답 내용이 아니라
    # 요청 성공 여부를 나타내는 HTTP 상태 코드만 간단히 출력된다.
    # 예: <Response [200]> → Square API 요청 성공
    print("http_response : ", http_response)

    # 성공 결과 확인
    if http_response.status_code == 200:

        response_body = http_response.json()

        # response는 JSON 응답 내용을 변환한 Python 딕셔너리 log로 찍고,
        print( "RESULT OF CREATE SQUARE PRODUCT (response body) : ",
            json.dumps(
                response_body,
                indent=2,
                ensure_ascii=False
            )
        )

        # [2] VALUES GENERATED DURING TRANSFORMATION
        #
        # +----------------------------+-------------------------------+-----------------------------+
        # | Square Field               | Generated Value               | Purpose                     |
        # +----------------------------+-------------------------------+-----------------------------+
        # | type                       | "ITEM"                        | Catalog object type         |
        # | id                         | "#item_<product_id>"          | Temporary item ID           |
        # | variation.type             | "ITEM_VARIATION"              | Variation object type       |
        # | variation.id               | "#variation_<product_id>"     | Temporary variation ID      |
        # | variation.name             | "Regular"                     | Default variation name      |
        # | pricing_type               | "FIXED_PRICING"               | Fixed product price         |
        # | currency                   | "CAD"                         | Canadian Dollar             |
        # +----------------------------+-------------------------------+-----------------------------+

        item_id = response_body["catalog_object"]["id"]

        variation_id = (
            response_body["catalog_object"]
            ["item_data"]
            ["variations"][0]
            ["id"]
        )

        print(f"          ITEM ID: {item_id}")
        print(f"          VARIATION ID: {variation_id}")

        # SQUARE에 상품생성 성공 후, 연동결과를 원데이터에 업데이트한다
        # Try Catch 문으로 sync를 위한 csv 파일 업데이트가 불가하면, Square 상품삭제 api 요청한다.
        try:

            square_variation = (
                response_body["catalog_object"]["item_data"]["variations"][0]
            )

            # Square 요청 JSON에서 임시 ITEM ID를 가져온다.
            temporary_item_id = square_product["object"]["id"]
            print("temporary_item_id >>>>", square_product["object"]["id"])
            # ex) #p002-item

            product_id = (
                temporary_item_id
                .removeprefix("#")
                .removesuffix("-item")
            )

            print("product_id >>>>", product_id)

            # product_id = square_product["id"]
            sku = square_variation["item_variation_data"]["sku"]
            square_catalog_object_id = square_variation["id"]
            sync_status = "SUCCESS"

            save_product_mapping(
                product_id=product_id,
                sku=sku,
                square_catalog_object_id=square_catalog_object_id,
                sync_status=sync_status,
            )

            print("Source product CSV updated successfully")

        except Exception as save_error:
            print("CSV mapping save failed:", save_error)
            print("Starting Square rollback...")

            # CSV 저장에 실패했으므로 방금 생성한 Square 상품 삭제
            delete_product(
                square_item_id=item_id,
                headers=headers,
            )

            # 오류가 없었던 것처럼 넘어가지 않고 다시 위로 전달
            raise RuntimeError(
                "CSV 저장에 실패하여 Square 상품을 삭제했습니다."
            ) from save_error


    else:
        # SQUARE API 연동실패시 log에 남기기
        print(http_response.status_code)
        print(http_response.json())



print("\n===== RESULT =====")

"""
Square 상품생성 API response 
{
  "catalog_object": {
    "type": "ITEM",
    "id": "5QIDQFB3JIC5KD4PGQMO3CW6",
    "updated_at": "2026-09-12T06:10:52.037Z",
    "created_at": "2026-09-12T06:10:52.037Z",
    "version": 1789193452037,
    "is_deleted": false,
    "present_at_all_locations": true,

    "item_data": {
      "name": "Golden Caramel Crunch",
      "description": "Buttery caramel shards in milk chocolate.",
      "is_taxable": true,

      "variations": [
        {
          "type": "ITEM_VARIATION",
          "id": "GXPNHM3FTRISRFOAZOD2KJPS",
          "updated_at": "2026-09-12T06:10:52.037Z",
          "created_at": "2026-09-12T06:10:52.037Z",
          "version": 1789193452037,
          "is_deleted": false,
          "present_at_all_locations": true,

          "item_variation_data": {
            "item_id": "5QIDQFB3JIC5KD4PGQMO3CW6",
            "name": "Regular",
            "sku": "CCF-BAR-003",
            "ordinal": 0,
            "pricing_type": "FIXED_PRICING",

            "price_money": {
              "amount": 795,
              "currency": "CAD"
            },

            "sellable": true,
            "stockable": true
          }
        }
      ],

      "product_type": "REGULAR",
      "description_html": "<p>Buttery caramel shards in milk chocolate.</p>",
      "description_plaintext": "Buttery caramel shards in milk chocolate.",
      "is_archived": false
    }
  },

  "id_mappings": [
    {
      "client_object_id": "#p003-item",
      "object_id": "5QIDQFB3JIC5KD4PGQMO3CW6"
    },
    {
      "client_object_id": "#p003-variation",
      "object_id": "GXPNHM3FTRISRFOAZOD2KJPS"
    }
  ]
}
"""

MAPPING_FILE = Path(
    "data/processed/product_square_mapping.csv"
)


# # Square API Mapping result 저장 product_square_mapping.csv
# def save_product_mapping(
#     product_id: str,
#     sku: str,
#     square_catalog_object_id: str | None,
#     sync_status: str,
# ) -> None:
#     new_record = pd.DataFrame(
#         [
#             {
#                 "product_id": product_id,
#                 "sku": sku,
#                 "square_catalog_object_id": square_catalog_object_id,
#                 "square_sync_status": sync_status,
#                 "square_synced_at": (
#                     datetime.now(timezone.utc).isoformat()
#                     if sync_status == "SUCCESS"
#                     else None
#                 ),
#             }
#         ]
#     )
#     print("new_record for syn", new_record)
#     print("MAPPING_FILE exists T or F >> ", MAPPING_FILE.exists())
#
#     if MAPPING_FILE.exists():
#         existing_df = pd.read_csv(MAPPING_FILE)
#
#         mapping_df = pd.concat(
#             [existing_df, new_record],
#             ignore_index=True,
#         )
#
#         mapping_df = mapping_df.drop_duplicates(
#             subset=["product_id"],
#             keep="last",
#         )
#     else:
#         mapping_df = new_record
#
#     MAPPING_FILE.parent.mkdir(
#         parents=True,
#         exist_ok=True,
#     )
#
#     mapping_df.to_csv(
#         MAPPING_FILE,
#         index=False,
#     )


PRODUCTS_FILE = RAW_DATA_DIR / "products_export.csv"

# 원본 CSV의 실제 구분자와 같아야 함.
# load_csv()에서 사용하는 구분자를 확인해서 맞춰줘.
CSV_SEPARATOR = ";"

def save_product_mapping(
    product_id: str,
    sku: str,
    square_catalog_object_id: str | None,
    sync_status: str,
) -> None:
    # 문자열로 읽어서 상품 코드, 앞자리 0, 빈 값 등을 유지한다.
    products_df = pd.read_csv(
        PRODUCTS_FILE,
        sep=CSV_SEPARATOR,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
    )

    if "sku" not in products_df.columns:
        raise ValueError(
            "CSV에 sku 컬럼이 없습니다. 컬럼명과 구분자를 확인하세요."
        )

    # 업데이트할 상품 찾기
    matched_rows = products_df["sku"].eq(str(sku))
    matched_count = int(matched_rows.sum())

    # 없거나 여러 행이면 잘못된 행을 수정하지 않고 중단
    if matched_count != 1:
        raise ValueError(
            f"SKU '{sku}'에 해당하는 행이 {matched_count}개입니다. "
            "원본 CSV에 정확히 1개 있어야 합니다."
        )

    sync_columns = [
        "square_catalog_object_id",
        "square_sync_status",
        "square_synced_at",
        "square_sync_error",
    ]

    # 동기화 컬럼이 없으면 추가
    for column in sync_columns:
        if column not in products_df.columns:
            products_df[column] = ""

    products_df.loc[
        matched_rows, "square_catalog_object_id"
    ] = square_catalog_object_id or ""

    products_df.loc[
        matched_rows, "square_sync_status"
    ] = sync_status

    if sync_status == "SUCCESS":
        products_df.loc[
            matched_rows, "square_synced_at"
        ] = datetime.now(timezone.utc).isoformat()

        products_df.loc[
            matched_rows, "square_sync_error"
        ] = ""

    # 먼저 임시 파일에 저장한 뒤 원본을 교체한다.
    # 쓰기 도중 실패해서 원본이 일부만 저장되는 상황을 줄인다.
    temporary_path = PRODUCTS_FILE.with_name(
        f"{PRODUCTS_FILE.name}.tmp"
    )

    try:
        products_df.to_csv(
            temporary_path,
            sep=CSV_SEPARATOR,
            index=False,
            encoding="utf-8-sig",
        )

        temporary_path.replace(PRODUCTS_FILE)

    finally:
        if temporary_path.exists():
            temporary_path.unlink()

    print(
        f"[CSV UPDATED] product_id={product_id}, "
        f"sku={sku}, status={sync_status}"
    )

"""
    CSV 저장 등 후속 처리에 실패했을 때
    방금 생성한 Square 상품을 삭제한다.
    """
# Square product delete API
def delete_product(
    square_item_id: str,
    headers: dict,
) -> None:
    print("access delete_product() >>>>>>>>> ")
    delete_url = (
        "https://connect.squareupsandbox.com"
        f"/v2/catalog/object/{square_item_id}"
    )

    delete_response = requests.delete(
        delete_url,
        headers=headers,
        timeout=30,
    )

    # 삭제 요청이 실패하면 예외를 발생시킨다.
    delete_response.raise_for_status()

    print(
        "ROLLBACK SUCCESS - Square product deleted:",
        square_item_id,
    )