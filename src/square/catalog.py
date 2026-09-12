# Square Catalog API 통신만 담당
import requests

from src.square.client import headers

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

    matched_ids = data.get("matched_variation_ids", [])

    if matched_ids:
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

# 상품생성
def create_product(square_product):

    create_url = "https://connect.squareupsandbox.com/v2/catalog/object"

    # Square에 상품 생성
    create_response = requests.post(
        create_url,
        headers=headers,
        json=square_product
    )

    # 성공 결과 확인
    if create_response.status_code == 200:

        data = create_response.json()

        print(data)

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

        item_id = data["catalog_object"]["id"]

        variation_id = (
            data["catalog_object"]
            ["item_data"]
            ["variations"][0]
            ["id"]
        )

        print(f"          ITEM ID: {item_id}")
        print(f"          VARIATION ID: {variation_id}")

        # created_count += 1

    else:
        print(create_response.status_code)
        print(create_response.json())



print("\n===== RESULT =====")

"""
Square에 요청한 payload 예시
{
  "idempotency_key": "4b69b6e3-a9e9-494b-9a56-c9110f81ae62",

  "object": {
    "type": "ITEM",
    "id": "#p003-item",

    "item_data": {
      "name": "Golden Caramel Crunch",
      "description": "Buttery caramel shards in milk chocolate.",

      "variations": [
        {
          "type": "ITEM_VARIATION",
          "id": "#p003-variation",

          "item_variation_data": {
            "name": "Regular",
            "sku": "CCF-BAR-003",
            "pricing_type": "FIXED_PRICING",

            "price_money": {
              "amount": 795,
              "currency": "CAD"
            },

            "item_id": "#p003-item"
          }
        }
      ]
    }
  }
}

# Square 상품생성 API response 
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