from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from src.square.client import headers


# 원본 고객 ID로 Square에 이미 등록된 고객인지 확인
def search_customer_by_reference_id(customer_id: str) -> bool:
    if not isinstance(customer_id, str) or not customer_id.strip():
        raise ValueError("검색할 원본 고객 ID가 필요합니다.")

    search_url = (
        "https://connect.squareupsandbox.com"
        "/v2/customers/search"
    )

    body = {
        "query": {
            "filter": {
                "reference_id": {
                    "exact": customer_id
                }
            }
        }
    }

    response = requests.post(
        search_url,
        headers=headers,
        json=body,
        timeout=30,
    )

    # 검색 실패를 '고객 없음'으로 처리하지 않고 중단
    response.raise_for_status()

    data = response.json()

    if data.get("errors"):
        raise RuntimeError(
            f"Square 고객 검색 실패: {data['errors']}"
        )

    customers = data.get("customers", [])

    return bool(customers)

# Square > Customer 생성
def create_customer(square_customer: dict) -> dict:
    create_url = (
        "https://connect.squareupsandbox.com"
        "/v2/customers"
    )

    response = requests.post(
        create_url,
        headers=headers,
        json=square_customer,
        timeout=30,
    )

    response_body = response.json()

    # API 실패 시 오류 내용을 포함해 중단
    if not response.ok or response_body.get("errors"):
        raise RuntimeError(
            f"Square 고객 생성 실패 "
            f"(HTTP {response.status_code}): "
            f"{response_body.get('errors', response_body)}"
        )

    customer = response_body.get("customer")

    if not customer or not customer.get("id"):
        raise RuntimeError(
            "Square 응답에 생성된 고객 ID가 없습니다."
        )

    print("[SUCCESS] Square customer created")
    print("Square customer ID:", customer["id"])
    print("Source customer ID:", customer.get("reference_id"))

    return customer

def update_customer_sync(
    customers_path: Path,
    customer_id: str,
    square_customer_id: str,
) -> None:
    if not square_customer_id:
        raise ValueError("저장할 Square 고객 ID가 없습니다.")

    # 전체 원본 고객 데이터 읽기
    customers_df = pd.read_csv(
        customers_path,
        sep=";",
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
    )

    # 원본 고객 ID로 업데이트할 행 찾기
    matched_rows = customers_df["id"].eq(str(customer_id))

    if matched_rows.sum() != 1:
        raise ValueError(
            f"고객 ID '{customer_id}'에 해당하는 행이 "
            f"{matched_rows.sum()}개입니다. 정확히 1개여야 합니다."
        )

    # 성공한 결과만 업데이트
    customers_df.loc[
        matched_rows, "square_customer_id"
    ] = square_customer_id

    customers_df.loc[
        matched_rows, "square_sync_status"
    ] = "SUCCESS"

    customers_df.loc[
        matched_rows, "square_synced_at"
    ] = datetime.now(timezone.utc).isoformat()

    customers_df.loc[
        matched_rows, "square_sync_error"
    ] = ""

    # 임시 파일 저장이 끝난 후 원본 교체
    temporary_path = customers_path.with_name(
        f"{customers_path.name}.tmp"
    )

    try:
        customers_df.to_csv(
            temporary_path,
            sep=";",
            index=False,
            encoding="utf-8-sig",
        )

        temporary_path.replace(customers_path)

    finally:
        if temporary_path.exists():
            temporary_path.unlink()

    print(f"[CSV UPDATED] Customer: {customer_id}")



# Square customer delete API
def delete_customer(square_customer_id: str) -> None:
    if not square_customer_id:
        raise ValueError("삭제할 Square 고객 ID가 없습니다.")

    delete_url = (
        "https://connect.squareupsandbox.com"
        f"/v2/customers/{square_customer_id}"
    )

    response = requests.delete(
        delete_url,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    # 응답 본문이 있는 경우 API 오류도 확인
    if response.content:
        response_body = response.json()

        if response_body.get("errors"):
            raise RuntimeError(
                f"Square 고객 삭제 실패: {response_body['errors']}"
            )

    print(
        "[ROLLBACK SUCCESS] Square customer deleted:",
        square_customer_id,
    )
