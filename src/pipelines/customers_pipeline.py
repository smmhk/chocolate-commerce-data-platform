from src.config.paths import RAW_DATA_DIR
from src.extract.load_csv import load_csv
from src.square.customers import (
    create_customer,
    search_customer_by_reference_id,
    update_customer_sync,
)
from src.transform.customers import transform_customer


def run_customers_pipeline():
    # =========================
    # 1. CSV Load
    # =========================
    customers_path = RAW_DATA_DIR / "customers_export.csv"
    addresses_path = RAW_DATA_DIR / "customer_addresses_export.csv"

    customers_df = load_csv(customers_path)
    addresses_df = load_csv(addresses_path)

    print("전체 고객 수:", len(customers_df))
    print("전체 주소 수:", len(addresses_df))

    # 가입경로 POS인 회원만 Square로 이동
    customers_df = customers_df[
        customers_df["signup_channel"]
        .astype("string")
        .str.strip()
        .str.upper()
        .eq("POS")
        .fillna(False)
    ].copy()

    print("전체 중 POS 가입고객 수:", len(customers_df))
    print("전체 중 POS 가입고객주소 수:", len(customers_df))

    success_count = 0
    skipped_count = 0
    failed_count = 0

    # =========================
    # 2. 고객별 Square 연동
    # =========================
    for _, customer_row in customers_df.iterrows():
        customer_id = customer_row["id"]
        square_customer_id = None

        print(f"\n=== Customer: {customer_id} ===")

        try:
            # 3. Square Payload 변환
            payload = transform_customer(
                customer_row=customer_row,
                addresses_df=addresses_df,
            )

            # 4. Duplicate Check
            already_exists = search_customer_by_reference_id(
                customer_id
            )

            if already_exists:
                print("⏭️ 이미 Square에 등록된 고객입니다.")
                skipped_count += 1
                continue

            # 5. Square Customer 생성
            square_customer = create_customer(payload)
            square_customer_id = square_customer["id"]

            print(
                "✅ Square Customer 생성 완료:",
                square_customer_id,
            )

            # 6. Local CSV Sync 정보 저장
            update_customer_sync(
                customers_path=customers_path,
                addresses_path=addresses_path,
                customer_id=customer_id,
                square_customer_id=square_customer_id,
            )

            success_count += 1
            print("✅ Local CSV Sync 정보 저장 완료")

        except Exception as error:
            failed_count += 1
            print(f"❌ 고객 {customer_id} 처리 실패: {error}")

            if square_customer_id is not None:
                print(
                    "⚠️ Square 고객은 생성되었지만 "
                    "로컬 CSV 저장을 완료하지 못했습니다."
                )
                print("Square Customer ID:", square_customer_id)

    # =========================
    # 7. 실행 결과
    # =========================
    print("\n=== Customers Pipeline Result ===")
    print(f"성공: {success_count}")
    print(f"중복 건너뜀: {skipped_count}")
    print(f"실패: {failed_count}")

    return {
        "success": success_count,
        "skipped": skipped_count,
        "failed": failed_count,
    }


if __name__ == "__main__":
    run_customers_pipeline()