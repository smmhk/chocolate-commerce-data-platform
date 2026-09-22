from src.config.paths import RAW_DATA_DIR
from src.extract.load_csv import load_csv
from src.transform.locations import transform_store
from src.square.location import (
    list_locations,
    create_location,
    update_store_sync,
)


# =========================
# 1. CSV Load
# =========================
stores_path = RAW_DATA_DIR / "stores_export.csv"
stores_df = load_csv(stores_path)

print("전체 매장 수:", len(stores_df))


# =========================
# 2. 미연동 매장 선택
# =========================
location_ids = (
    stores_df["square_location_id"]
    .astype("string")
    .fillna("")
    .str.strip()
)

pending_stores_df = stores_df[location_ids.eq("")].copy()

print("미연동 매장 수:", len(pending_stores_df))

if pending_stores_df.empty:
    print("모든 매장의 Location ID가 저장되어 있습니다.")
    raise SystemExit(0)

# 미연동 매장 중 첫 번째 한 건만 테스트
store_row = pending_stores_df.iloc[0]

store_row_id = store_row["id"]
store_code = store_row["store_id"]
store_name = str(store_row["store_name"]).strip()

print("\n=== Test Store ===")
print("Store ID:", store_row_id)
print("Store Code:", store_code)
print("Store Name:", store_name)


# =========================
# 3. Square Location 조회 및 이름 비교
# =========================
square_locations = list_locations()

matches = [
    location
    for location in square_locations
    if location.get("name", "").strip() == store_name
]

if len(matches) > 1:
    raise ValueError(
        f"같은 이름의 Location이 여러 개입니다: {store_name}"
    )


# =========================
# 4. 기존 매장 연결 또는 새 매장 생성
# =========================
if matches:
    square_location = matches[0]

    if square_location.get("status") != "ACTIVE":
        raise ValueError(
            "기존 매장이 비활성 상태입니다. 확인이 필요합니다: "
            f"{square_location['id']}"
        )

    print("\n✅ 기존 Square 매장 발견")

else:
    payload = transform_store(store_row)

    print("\n=== Square Location Payload ===")
    print(payload)

    square_location = create_location(payload)

    print("\n✅ Square 매장 생성 완료")

square_location_id = square_location["id"]

print("Square Location ID:", square_location_id)


# =========================
# 5. Local CSV Sync 정보 저장
# =========================
try:
    update_store_sync(
        stores_path=stores_path,
        store_row_id=store_row_id,
        square_location_id=square_location_id,
    )
except Exception:
    print(
        "\n❌ CSV 저장 실패. Square 매장은 유지됩니다.\n"
        f"Store Code: {store_code}\n"
        f"Square Location ID: {square_location_id}"
    )
    raise

print("\n✅ CSV 연동 정보 저장 완료")


# =========================
# 6. 저장 결과 확인
# =========================
saved_stores_df = load_csv(stores_path)

saved_row = saved_stores_df.loc[
    saved_stores_df["id"].eq(store_row_id)
].iloc[0]

if saved_row["square_location_id"] != square_location_id:
    raise ValueError("CSV에 저장된 Square Location ID가 다릅니다.")

if saved_row["square_sync_status"] != "SUCCESS":
    raise ValueError("CSV의 동기화 상태가 SUCCESS가 아닙니다.")

print("\n=== Saved Store ===")
print(
    saved_row[
        [
            "store_id",
            "store_name",
            "square_location_id",
            "square_sync_status",
            "square_synced_at",
        ]
    ]
)

print("\n✅ 매장 한 건 연동 및 CSV 저장 확인 완료")