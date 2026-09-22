from src.square.location import list_locations, create_location, update_store_sync

from src.config.paths import RAW_DATA_DIR
from src.extract.load_csv import load_csv
from src.transform.locations import transform_store

stores_path = RAW_DATA_DIR / "stores_export.csv"


stores_df = load_csv(stores_path)

total_count = len(stores_df)
print(f"Total stores to check: {total_count}")

# square_location_id is null 인 store list 조회 후,
# store_name으로 square에 이미 저장되어 있는 매장인지 한번 더 중복확인 후
# 있으면, square_location_id를 update
# 없으면, square에 연동 후 csv 파일 내 square_location_id를 update
location_ids = (
    stores_df["square_location_id"]
    .astype("string")
    .fillna("")
    .str.strip()
)

pending_stores_df = stores_df[location_ids.eq("")].copy()

# Square 매장 목록은 한 번만 조회
square_locations = list_locations()

for _, store_row in pending_stores_df.iterrows():
    store_name = str(store_row["store_name"]).strip()

    # 같은 이름을 가진 Location 찾기
    matches = [
        location
        for location in square_locations
        if location.get("name", "").strip() == store_name
    ]

    print(f"\n매장명: {store_name}")

    if len(matches) > 1:
        raise ValueError(
            f"같은 이름의 Location이 여러 개입니다: {store_name}"
        )

    if matches:
        matched_location = matches[0]
        square_location_id = matched_location["id"]

        print("✅ 기존 Square 매장 발견")
        print("Square Location ID:", square_location_id)
        print("상태:", matched_location.get("status"))

        # 이 ID를 CSV에 저장
        try:
            update_store_sync(
                stores_path=stores_path,
                store_row_id=store_row["id"],
                square_location_id=square_location_id,
            )
        except Exception:
            print(
                "CSV 저장 실패. Square 매장은 유지됩니다.\n"
                f"재연결할 Location ID: {square_location_id}"
            )
            raise

        print("✅ CSV 연동 정보 저장 완료 (update)")

    else:
        print("미등록 매장: 이름이 일치하는 Location 없음")

        # Square에 생성 후 ID를 CSV에 저장
        payload = transform_store(store_row)
        square_location = create_location(payload)

        # 이번 실행에서 생성한 매장도 비교 목록에 추가
        square_locations.append(square_location)

        print("✅ Square 매장 생성 완료")

    square_location_id = square_location["id"]
    print("Square Location ID:", square_location_id)

    try:
        update_store_sync(
            stores_path=stores_path,
            store_row_id=store_row["id"],
            square_location_id=square_location_id,
        )
    except Exception:
        print(
            "CSV 저장 실패. Square 매장은 유지됩니다.\n"
            f"재연결할 Location ID: {square_location_id}"
        )
        raise

    print("✅ CSV 연동 정보 저장 완료(create)")


