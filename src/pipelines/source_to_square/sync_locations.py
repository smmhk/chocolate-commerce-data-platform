from src.clients.square.locations import (
    list_locations,
    create_location,
    update_store_sync,
)
from src.config.paths import get_online_source_dir
from src.extract.csv_reader import load_csv
from src.transform.square.locations_payload import transform_store


def run_locations_pipeline():
    stores_path = get_online_source_dir() / "stores_export.csv"
    stores_df = load_csv(stores_path)

    # Square ID가 없는 매장만 연동 대상으로 선택
    location_ids = (
        stores_df["square_location_id"]
        .astype("string")
        .fillna("")
        .str.strip()
    )
    pending_stores_df = stores_df[location_ids.eq("")].copy()

    print(f"[SOURCE] {stores_path}")
    print(f"[TOTAL] {len(stores_df)}")
    print(f"[PENDING] {len(pending_stores_df)}")
    print(f"[SKIPPED] {len(stores_df) - len(pending_stores_df)}")

    if pending_stores_df.empty:
        print("[SKIP] 모든 매장에 Square ID가 있어 CSV 업데이트를 건너뜁니다.")
    else:
        # Square 매장 목록은 한 번만 조회
        square_locations = list_locations()

        for _, store_row in pending_stores_df.iterrows():
            store_name = str(store_row["store_name"]).strip()

            matches = [
                location
                for location in square_locations
                if location.get("name", "").strip() == store_name
            ]

            print(f"\n[STORE] {store_name}")

            if len(matches) > 1:
                raise ValueError(
                    f"같은 이름의 Location이 여러 개입니다: {store_name}"
                )

            if matches:
                square_location = matches[0]
                print(f"[EXISTS] 기존 Square 매장 연결: {square_location['id']}")
            else:
                payload = transform_store(store_row)
                square_location = create_location(payload)
                square_locations.append(square_location)
                print(f"[CREATED] Square 매장 생성: {square_location['id']}")

            square_location_id = square_location["id"]

            try:
                update_store_sync(
                    stores_path=stores_path,
                    store_row_id=store_row["id"],
                    square_location_id=square_location_id,
                )
            except Exception:
                print(
                    "[ERROR] CSV 저장 실패. Square 매장은 유지됩니다.\n"
                    f"재연결할 Location ID: {square_location_id}"
                )
                raise

            print(
                f"[CSV UPDATED] {store_name} → {square_location_id}"
            )

    # 파일을 다시 읽어서 실제 저장된 결과 출력
    updated_df = load_csv(stores_path)

    print("\n[RESULT] 현재 CSV 연동 정보")
    print(
        updated_df[
            ["store_name", "square_location_id", "square_sync_status"]
        ].to_string(index=False)
    )
    print("[DONE] 매장 연동 처리 완료")


if __name__ == "__main__":
    run_locations_pipeline()