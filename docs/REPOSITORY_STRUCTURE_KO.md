# 폴더 구조와 실행 경로 변경 안내

이번 변경은 파일 배치·이름·import·실행 경로를 정리합니다. 금액 변환, 필터 조건, SQL, API 요청과 오류 처리 같은 업무 로직은 유지했습니다.

## 구조

```text
chocolate-commerce-data-platform/
├── src/
│   ├── clients/square/           # Square API 통신과 인증 설정
│   ├── common/logging.py        # 공통 로그와 실행 메타데이터
│   ├── config/paths.py          # 프로젝트 기준 경로
│   ├── extract/                 # CSV 읽기
│   │   ├── csv_reader.py
│   │   └── online/read_source_tables.py
│   ├── transform/
│   │   ├── online/select_channel_records.py
│   │   └── square/*_payload.py  # Square 요청 데이터 변환
│   ├── load/postgres/
│   │   ├── connection.py
│   │   ├── online/replace_table.py
│   │   └── square/upsert_*.py
│   ├── snapshots/               # CSV 추출·BigQuery 비교 공통 구현
│   │   ├── online.py
│   │   └── square.py
│   └── pipelines/              # 실행 진입점
│       ├── source_to_square/   # CSV → Square 시뮬레이션 데이터 준비
│       ├── ingestion/          # 원천 → PostgreSQL
│       │   ├── online/
│       │   └── square/
│       ├── export/             # PostgreSQL → CSV
│       │   ├── online/
│       │   └── square/
│       └── validation/         # GCS CSV ↔ BigQuery 검증
│           ├── online/
│           └── square/
├── scripts/
│   ├── inspect/square/         # API 응답 조사
│   └── manual/square/          # 실제 API·CSV 변경이 있는 수동 연동 확인
├── tests/                      # 외부 서비스 없이 실행하는 자동 검사
├── data/sample/
├── sql/
├── chocolate_dbt/
├── docs/
├── docker-compose.yml
└── requirements.txt
```

## 이름 규칙과 책임

- `sync_*`: 원본 데이터를 Square에 생성·연결합니다. 분석용 수집과 구분합니다.
- `load_*_to_postgres`: 원천에서 읽고 PostgreSQL에 적재합니다.
- `export_*_to_csv`: PostgreSQL 데이터를 CSV 파일로 내보냅니다. GCS 업로드는 Kestra 작업에서 수행합니다.
- `validate_*_in_bigquery`: GCS의 CSV와 BigQuery 데이터를 비교합니다.
- `replace_*` / `upsert_*`: 실제 DB 저장 전략을 이름에 표시합니다.
- `clients`: API 통신, `transform`: 변환, `load`: DB 쓰기, `pipelines`: 실행 순서를 담당합니다.
- `snapshots`: 추출과 비교를 공유하는 기존 구현입니다. export와 validation 양쪽에서 사용하며, Square 모듈의 기존 export/validate CLI도 유지합니다.

기존 상품 변환 함수의 API 호출 등 책임 분리가 덜 된 부분은 다음 리팩터링 대상으로 남겨 두었습니다. 이번 파일 이동에서 동작을 함께 바꾸지 않았습니다.

## 실행 예시

프로젝트 루트에서 `python -m`으로 실행합니다. 필요한 의존성, CSV, DB 스키마와 자격증명은 기존과 동일합니다.

```bash
# 온라인 → PostgreSQL
python -m src.pipelines.ingestion.online.load_tables_to_postgres --tables products

# Square → PostgreSQL
python -m src.pipelines.ingestion.square.load_orders_to_postgres

# PostgreSQL → CSV
python -m src.pipelines.export.online.export_products_to_csv --output-dir ./exports

# GCS CSV ↔ BigQuery
python -m src.pipelines.validation.online.validate_products_in_bigquery --gcs-uri gs://BUCKET/OBJECT.csv

# 원본 → Square: 외부 데이터 생성 및 로컬 CSV 변경
python -m src.pipelines.source_to_square.sync_orders

# 수동 연동 확인: 외부 데이터 생성 및 로컬 CSV 변경
python -m scripts.manual.square.create_orders

# 구조 검사: 외부 API·DB 연결 없이 실행
python -m unittest discover -s tests -v
```

## Kestra 전환

기존 경로의 호환 실행 파일은 남기지 않았습니다. 이 수정본을 배치할 때 Kestra UI에 저장된 `python -m ...` 명령도 아래 새 모듈 경로로 변경해야 합니다. Flow ID, 테이블 이름, CLI 옵션은 그대로 사용할 수 있습니다. 이번 작업에서 실제 Kestra 인스턴스는 변경하지 않았습니다.

과거 실행 로그는 당시 경로를 보존합니다. 문서의 코드 참조와 실행 예시는 새 경로를 사용합니다. 과거 patch 파일은 적용용이 아닌 기록 자료이며 새 구조에 그대로 적용하면 안 됩니다.

## 파일 이동 대응표

| 이전 파일 | 새 파일 |
|---|---|
| `src/pipelines/run_logging.py` | `src/common/logging.py` |
| `src/pipelines/online_raw_snapshot.py` | `src/snapshots/online.py` |
| `src/pipelines/square_raw_snapshot.py` | `src/snapshots/square.py` |
| `src/pipelines/online_to_postgres.py` | `src/pipelines/ingestion/online/load_tables_to_postgres.py` |
| `src/extract/load_csv.py` | `src/extract/csv_reader.py` |
| `src/extract/online/load_online_data.py` | `src/extract/online/read_source_tables.py` |
| `src/transform/online/filter_online_data.py` | `src/transform/online/select_channel_records.py` |
| `src/load/postgres/load_table.py` | `src/load/postgres/online/replace_table.py` |
| `src/extract/online/_init_.py` | `src/extract/online/__init__.py` |
| `src/transform/online/_init_.py` | `src/transform/online/__init__.py` |
| `src/pipelines/products_pipeline.py` | `src/pipelines/source_to_square/sync_products.py` |
| `src/transform/products.py` | `src/transform/square/products_payload.py` |
| `tests/test_products.py` | `scripts/manual/square/create_products.py` |
| `src/square/catalog.py` | `src/clients/square/catalog.py` |
| `src/pipelines/customers_pipeline.py` | `src/pipelines/source_to_square/sync_customers.py` |
| `src/transform/customers.py` | `src/transform/square/customers_payload.py` |
| `tests/test_customers.py` | `scripts/manual/square/create_customers.py` |
| `src/square/customers.py` | `src/clients/square/customers.py` |
| `src/pipelines/orders_pipeline.py` | `src/pipelines/source_to_square/sync_orders.py` |
| `src/transform/orders.py` | `src/transform/square/orders_payload.py` |
| `tests/test_orders.py` | `scripts/manual/square/create_orders.py` |
| `src/square/orders.py` | `src/clients/square/orders.py` |
| `src/pipelines/stores_pipeline.py` | `src/pipelines/source_to_square/sync_locations.py` |
| `src/transform/locations.py` | `src/transform/square/locations_payload.py` |
| `tests/test_locations.py` | `scripts/manual/square/create_locations.py` |
| `src/square/location.py` | `src/clients/square/locations.py` |
| `src/square/client.py` | `src/clients/square/config.py` |
| `src/pipelines/square_catalog_to_postgres.py` | `src/pipelines/ingestion/square/load_catalog_objects_to_postgres.py` |
| `src/load/postgres/load_square_catalog.py` | `src/load/postgres/square/upsert_catalog_objects.py` |
| `src/pipelines/square_customers_to_postgres.py` | `src/pipelines/ingestion/square/load_customers_to_postgres.py` |
| `src/load/postgres/load_square_customers.py` | `src/load/postgres/square/upsert_customers.py` |
| `src/pipelines/square_locations_to_postgres.py` | `src/pipelines/ingestion/square/load_locations_to_postgres.py` |
| `src/load/postgres/load_square_locations.py` | `src/load/postgres/square/upsert_locations.py` |
| `src/pipelines/square_orders_to_postgres.py` | `src/pipelines/ingestion/square/load_orders_to_postgres.py` |
| `src/load/postgres/load_square_orders.py` | `src/load/postgres/square/upsert_orders.py` |
| `src/pipelines/online_products_to_file.py` | `src/pipelines/export/online/export_products_to_csv.py` |
| `src/pipelines/validate_products_load.py` | `src/pipelines/validation/online/validate_products_in_bigquery.py` |
| `src/pipelines/online_customers_to_file.py` | `src/pipelines/export/online/export_customers_to_csv.py` |
| `src/pipelines/validate_online_customers_load.py` | `src/pipelines/validation/online/validate_customers_in_bigquery.py` |
| `src/pipelines/online_customer_addresses_to_file.py` | `src/pipelines/export/online/export_customer_addresses_to_csv.py` |
| `src/pipelines/validate_online_customer_addresses_load.py` | `src/pipelines/validation/online/validate_customer_addresses_in_bigquery.py` |
| `src/pipelines/online_orders_to_file.py` | `src/pipelines/export/online/export_orders_to_csv.py` |
| `src/pipelines/validate_online_orders_load.py` | `src/pipelines/validation/online/validate_orders_in_bigquery.py` |
| `src/pipelines/online_order_items_to_file.py` | `src/pipelines/export/online/export_order_items_to_csv.py` |
| `src/pipelines/validate_online_order_items_load.py` | `src/pipelines/validation/online/validate_order_items_in_bigquery.py` |
| `src/pipelines/square_catalog_objects_to_file.py` | `src/pipelines/export/square/export_catalog_objects_to_csv.py` |
| `src/pipelines/validate_catalog_objects_load.py` | `src/pipelines/validation/square/validate_catalog_objects_in_bigquery.py` |
| `src/pipelines/square_customers_to_file.py` | `src/pipelines/export/square/export_customers_to_csv.py` |
| `src/pipelines/validate_customers_load.py` | `src/pipelines/validation/square/validate_customers_in_bigquery.py` |
| `src/pipelines/square_locations_to_file.py` | `src/pipelines/export/square/export_locations_to_csv.py` |
| `src/pipelines/validate_locations_load.py` | `src/pipelines/validation/square/validate_locations_in_bigquery.py` |
| `src/pipelines/square_orders_to_file.py` | `src/pipelines/export/square/export_orders_to_csv.py` |
| `src/pipelines/validate_orders_load.py` | `src/pipelines/validation/square/validate_orders_in_bigquery.py` |
| `src/pipelines/inspect_square_catalog.py` | `scripts/inspect/square/inspect_catalog.py` |
| `src/pipelines/inspect_square_customers.py` | `scripts/inspect/square/inspect_customers.py` |
| `src/pipelines/inspect_square_orders.py` | `scripts/inspect/square/inspect_orders.py` |
