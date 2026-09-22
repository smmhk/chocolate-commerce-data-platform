from datetime import timezone, datetime
from pathlib import Path

import pandas as pd
import requests
from src.square.client import headers

def list_locations():
    url = "https://connect.squareupsandbox.com/v2/locations"

    response = requests.get(
        url,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if data.get("errors"):
        raise RuntimeError(
            f"Square Location 조회 실패: {data['errors']}"
        )

    return data.get("locations", [])

def create_location(payload):
    response = requests.post(
        "https://connect.squareupsandbox.com/v2/locations",
        headers=headers,
        json=payload,
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            f"Square 매장 생성 실패 "
            f"({response.status_code}): {response.text}"
        )

    data = response.json()

    if data.get("errors"):
        raise RuntimeError(f"Square 오류: {data['errors']}")

    location = data.get("location")

    if not location or not location.get("id"):
        raise ValueError("생성 응답에 Location ID가 없습니다.")

    return location


def update_store_sync(stores_path, store_row_id, square_location_id):
    stores_path = Path(stores_path)

    # 빈 동기화 컬럼에도 문자열을 저장할 수 있도록 읽기
    stores_df = pd.read_csv(
        stores_path,
        sep=";",
        dtype=str,
        keep_default_na=False,
    )

    # CSV의 UUID 컬럼인 id로 정확한 행 선택
    mask = stores_df["id"].eq(str(store_row_id))

    if mask.sum() != 1:
        raise ValueError(
            f"저장 대상 매장은 정확히 한 행이어야 합니다: {store_row_id}"
        )

    stores_df.loc[mask, "square_location_id"] = square_location_id
    stores_df.loc[mask, "square_sync_status"] = "SUCCESS"
    stores_df.loc[mask, "square_synced_at"] = (
        datetime.now(timezone.utc).isoformat()
    )
    stores_df.loc[mask, "square_sync_error"] = ""

    # 임시 파일에 쓰기가 완료된 뒤 원본 교체
    temp_path = stores_path.with_suffix(".tmp")

    try:
        stores_df.to_csv(
            temp_path,
            sep=";",
            index=False,
            encoding="utf-8",
        )
        temp_path.replace(stores_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()