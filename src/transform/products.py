#  Lovable 데이터 -> Square API 가 요구하는 데이터형식으로 변화하는 작업 진행
import uuid

from src.square.catalog import create_product

def transform_product(df):
    # 1. 필요한 컬럼 확인/선택
    # 2. 결측값 처리
    # 3. 데이터 타입 변환
    # 4. 가격 등의 값 변환
    # 5. Lovable 필드 → Square 필드 mapping
    # 6. Square API에서 사용할 데이터 반환

    # =============================================================================
    # Lovable Products → Square Catalog Field Mapping
    # =============================================================================
    #
    # [1] SOURCE FIELD MAPPING
    #
    # +----------------------------+-----------------------------------------------+--------------------------+
    # | Lovable Source             | Square Target                                 | Transformation           |
    # +----------------------------+-----------------------------------------------+--------------------------+
    # | product_name               | item_data.name                                | Direct mapping           |
    # | description                | item_data.description_html                    | Direct mapping           |
    # | sku                        | variations[].item_variation_data.sku          | Direct mapping           |
    # | price                      | ...price_money.amount                         | price * 100              |
    # | category                   | item_data.categories[].id                     | Category lookup/create   |
    # | image_key                  | item_data.image_ids[]                         | Image lookup/create      |
    # | square_catalog_object_id   | CatalogObject.id                              | Save ID returned by      |
    # |                            |                                               | Square after creation    |
    # +----------------------------+-----------------------------------------------+--------------------------+
    #
    #
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
    #
    #
    # [3] SOURCE FIELDS NOT SENT TO SQUARE IN THE INITIAL VERSION
    #
    # +----------------------------+------------------------------------------------+
    # | Lovable Source             | Reason                                         |
    # +----------------------------+------------------------------------------------+
    # | id                         | Lovable internal database primary key          |
    # | product_id                 | Internal product ID / used for mapping          |
    # | is_best_seller             | No direct Square Catalog field                 |
    # | active_status              | No direct 1:1 mapping in initial version       |
    # | created_at                 | Source system metadata                         |
    # | updated_at                 | Source system metadata                         |
    # +----------------------------+------------------------------------------------+
    #
    # NOTE:
    # - category and image_key require Square object IDs, so they can be added later.
    # - square_catalog_object_id is not sent when creating a new product.
    #   Square returns the real CatalogObject.id after successful creation.
    # - Start with product_name, description, sku, and price for the first version.
    #
    # =============================================================================

    # Dataframe 형식의 row 1건 전달 받음.

    # Square JSON Mapping
    row = df.iloc[0]

    product_id = row["product_id"].lower()
    product_name = row["product_name"]
    description = row["description"]
    sku = row["sku"]
    price = row["price"]
    price_amount = int(price * 100)


    square_product = {
        "idempotency_key": str(uuid.uuid4()),
        "object": {
            "type": "ITEM",
            "id": f"#{product_id}-item",
            "item_data": {
                "name": product_name,
                "description": description,
                "variations": [
                    {
                        "type": "ITEM_VARIATION",
                        "id": f"#{product_id}-variation",
                        "item_variation_data": {
                            "name": "Regular",
                            "sku": sku,
                            "pricing_type": "FIXED_PRICING",
                            "price_money": {
                                "amount": price_amount,
                                "currency": "CAD"
                            },
                            "item_id": f"#{product_id}-item"
                        }
                    }
                ]
            }
        }
    }

    create_product(square_product)
    return square_product