import json

from src.square.catalog import list_catalog_items


def run():
    print("[START] Inspect Square catalog")

    items = list_catalog_items()

    if not items:
        print("[INFO] 조회된 상품이 없습니다.")
        return

    # 첫 상품의 전체 구조 확인
    print("\n===== FIRST ITEM =====")
    print(
        json.dumps(
            items[0],
            indent=2,
            ensure_ascii=False,
        )
    )

    # 전체 상품의 이름과 variation 정보 확인
    print("\n===== PRODUCT SUMMARY =====")

    for item in items:
        item_data = item.get("item_data", {})

        print(
            f"\n상품명: {item_data.get('name')}"
            f"\nITEM ID: {item['id']}"
        )

        for variation in item_data.get("variations", []):
            variation_data = variation.get(
                "item_variation_data", {}
            )
            price = variation_data.get("price_money", {})

            print(
                f"  SKU: {variation_data.get('sku')}"
                f" | Variation ID: {variation['id']}"
                f" | 금액(최소 통화 단위): {price.get('amount')}"
                f" | 통화: {price.get('currency')}"
            )

    print("\n[DONE] Inspect Square catalog")


if __name__ == "__main__":
    run()