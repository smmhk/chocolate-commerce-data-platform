-- Square API에서 수집한 원본 데이터를 저장할 스키마
CREATE SCHEMA IF NOT EXISTS raw_square;

-- 상품 JSON 원본 저장
-- 현재 ITEM만 수집하며, 하위 variations도 payload에 함께 보관
CREATE TABLE IF NOT EXISTS raw_square.catalog_objects (
    square_object_id TEXT PRIMARY KEY,
    object_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Square 고객 원본 저장
CREATE TABLE IF NOT EXISTS raw_square.customers (
    square_customer_id TEXT PRIMARY KEY,
    payload JSONB NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Square 주문 원본 저장
-- 주문상품·세금 등의 중첩 데이터도 payload에 함께 보관
CREATE TABLE IF NOT EXISTS raw_square.orders (
    square_order_id TEXT PRIMARY KEY,
    payload JSONB NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Square 매장 원본 저장
CREATE TABLE IF NOT EXISTS raw_square.locations (
    square_location_id TEXT PRIMARY KEY,
    payload JSONB NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);