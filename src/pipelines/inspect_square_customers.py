import json

from src.square.customers import list_customers


def run():
    print("[START] Inspect Square customers")

    customers = list_customers()

    if not customers:
        print("[INFO] 조회된 고객이 없습니다.")
        return

    # 첫 고객의 전체 JSON 구조 확인
    print("\n===== FIRST CUSTOMER =====")

    print(
        json.dumps(
            customers[0],
            indent=2,
            ensure_ascii=False,
        )
    )

    # 전체 고객의 Square ID와 원본 ID 연결 확인
    print("\n===== CUSTOMER SUMMARY =====")

    for customer in customers:
        name = " ".join(
            part
            for part in (
                customer.get("given_name"),
                customer.get("family_name"),
            )
            if part
        )

        print(
            f"Square ID: {customer['id']}"
            f" | Source ID: {customer.get('reference_id')}"
            f" | Name: {name}"
        )

    print("\n[DONE] Inspect Square customers")


if __name__ == "__main__":
    run()