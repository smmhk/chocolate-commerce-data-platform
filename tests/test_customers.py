import os
import sys

import pandas as pd

# # 프로젝트 root 경로 추가
# sys.path.append(
#     os.path.dirname(
#         os.path.dirname(
#             os.path.abspath(__file__)
#         )
#     )
# )
from src.config.paths import RAW_DATA_DIR, PROCESSED_DATA_DIR
from src.extract.load_csv import load_csv
from src.square.customers import create_customer, search_customer_by_reference_id, update_customer_sync
from src.transform.customers import transform_customer

pd.set_option("display.max_columns", None)   # 모든 컬럼 출력
pd.set_option("display.max_rows", None)      # 모든 행 출력
pd.set_option("display.max_colwidth", None)  # 긴 문자열도 생략하지 않음
pd.set_option("display.width", None)         # 화면 너비에 따른 컬럼 생략 방지

# =========================
# 1. CSV Load
# =========================

customers_path = RAW_DATA_DIR / "customers_export.csv"
customer_addresses_path = RAW_DATA_DIR / "customer_addresses_export.csv"

customers_df = load_csv(customers_path)

addresses_df = load_csv(customer_addresses_path)

print("전체 고객 수:", len(customers_df))
print("전체 주소 수:", len(addresses_df))

# POS 가입 고객만 선택 — 실제 컬럼명 확인 필요
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


# =========================
# 2. 테스트 고객 선택
# =========================

customer_row = customers_df.iloc[0]

customer_id = customer_row["id"]

print("\n=== Test Customer ===")
print("Customer ID:", customer_id)


# =========================
# 3. Square Payload 변환
# =========================

payload = transform_customer(
    customer_row=customer_row,
    addresses_df=addresses_df,
)

print("\n=== Square Customer Payload ===")
print(payload)


# =========================
# 4. Duplicate Check
# =========================

already_exists = search_customer_by_reference_id(
    customer_id
)

if already_exists:
    raise ValueError(
        f"Customer '{customer_id}'는 이미 Square에 등록되어 있습니다."
    )


print("\n✅ Square에 동일한 reference_id 고객 없음")


# =========================
# 5. Square Customer 생성
# =========================

square_customer = create_customer(payload)

square_customer_id = square_customer["id"]


print("\n✅ Square Customer 생성 완료")
print("Square Customer ID:", square_customer_id)


# =========================
# 6. Local CSV Sync 정보 저장
# =========================

update_customer_sync(
    customers_path=customers_path,
    addresses_path=customer_addresses_path,
    customer_id=customer_id,
    square_customer_id=square_customer_id,
)


print("\n✅ Customer end-to-end test passed.")