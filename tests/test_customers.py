import json
from uuid import uuid4

import pandas as pd

from src.config.paths import RAW_DATA_DIR
from src.extract.load_csv import load_csv
from src.transform.customers import transform_customer
from src.square.customers import delete_customer

from src.square.customers import (
    search_customer_by_reference_id,
    create_customer,
    update_customer_sync
)

pd.set_option("display.max_columns", None)
pd.set_option("display.max_colwidth", None)
pd.set_option("display.width", None)

customers_path = RAW_DATA_DIR / "customers_export.csv"

customers_df = load_csv(customers_path)

# 1. 실제 가입 경로 값 확인
print("Signup channels:")
print(customers_df["signup_channel"].value_counts(dropna=False))

# 2. POS에서 가입한 고객만 선택
# CSV에서 매장 가입 값이 RETAIL이라면 "RETAIL"로 변경
POS_SIGNUP_CHANNEL = "POS"

target_customers_df = customers_df.loc[
    customers_df["signup_channel"].eq(POS_SIGNUP_CHANNEL)
].copy()

if target_customers_df.empty:
    raise ValueError(
        f"signup_channel이 '{POS_SIGNUP_CHANNEL}'인 고객이 없습니다. "
        "출력된 가입 경로 값을 확인해주세요."
    )

# 3. 첫 번째 고객 한 명을 DataFrame으로 선택
customer_df = target_customers_df.iloc[[0]]

print("TEST TARGET CUSTOMER:")
print(customer_df)

# 4. 원본 고객 식별값 확인
customer_id = customer_df["id"].iloc[0]
customer_number = customer_df["customer_number"].iloc[0]

print("Target customer ID:", customer_id)
print("Target customer number:", customer_number)

# 5. Square에 이미 등록된 고객인지 확인
existing_customer = search_customer_by_reference_id(customer_id)

print("Existing customer:", existing_customer)

if existing_customer:
    print(f"[EXISTS] {customer_id}")



else:
    print(f"[NEW] {customer_id}")

    # 1. Square 요청 형식으로 변환
    square_customer = transform_customer(customer_df)

    # 새로운 고객 생성 요청에 사용할 키
    square_customer["idempotency_key"] = str(uuid4())

    # 2. 전송할 데이터 확인
    print("Square request payload:")
    print(
        json.dumps(
            square_customer,
            ensure_ascii=False,
            indent=4,
        )
    )

    # 3. Square Sandbox에 고객 생성
    created_customer = create_customer(square_customer)

    # 4. 생성된 Square 고객 ID 확인
    square_customer_id = created_customer["id"]
    print("Created Square customer ID:", square_customer_id)

    # Square 고객 생성
    created_customer = create_customer(square_customer)
    square_customer_id = created_customer["id"]

    # 생성 성공 후 원본 CSV 업데이트
    try:
        update_customer_sync(
            customers_path=customers_path,
            customer_id=customer_id,
            square_customer_id=square_customer_id,
        )

    except Exception as save_error:
        print("[CSV UPDATE FAILED]", save_error)
        print("Starting Square customer rollback...")

        try:
            delete_customer(square_customer_id)

        except Exception as delete_error:
            # 삭제까지 실패하면 두 오류와 고객 ID를 함께 남김
            raise RuntimeError(
                f"CSV 저장 실패: {save_error}\n"
                f"Square 고객 삭제도 완료 여부를 확인하지 못했습니다: "
                f"{delete_error}\n"
                f"확인할 Square 고객 ID: {square_customer_id}"
            ) from delete_error

        raise RuntimeError(
            "CSV 저장에 실패하여 생성한 Square 고객을 삭제했습니다."
        ) from save_error