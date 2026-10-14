-- =========================================================
-- Charlie's Chocolate Factory
-- Raw Online PostgreSQL Schema
-- =========================================================

CREATE SCHEMA IF NOT EXISTS raw_online;


-- =========================================================
-- 1. Products
-- =========================================================

CREATE TABLE IF NOT EXISTS raw_online.products (
    id                          VARCHAR(100),
    product_id                  VARCHAR(100),
    sku                         VARCHAR(100),
    product_name                VARCHAR(255),
    category                    VARCHAR(100),

    price                       NUMERIC(12, 2),

    image_key                   VARCHAR(255),
    description                 TEXT,

    is_best_seller              BOOLEAN,
    active_status               BOOLEAN,

    square_catalog_object_id    VARCHAR(100),

    created_at                  TIMESTAMPTZ,
    updated_at                  TIMESTAMPTZ,

    square_sync_status          VARCHAR(50),
    square_synced_at            TIMESTAMPTZ,
    square_sync_error           TEXT
);


-- =========================================================
-- 2. Customers
-- =========================================================

CREATE TABLE IF NOT EXISTS raw_online.customers (
    id                          VARCHAR(100),
    customer_number             VARCHAR(100),
    user_id                     VARCHAR(100),

    email                       VARCHAR(255),
    first_name                  VARCHAR(100),
    last_name                   VARCHAR(100),

    phone                       VARCHAR(50),

    customer_type               VARCHAR(50),

    square_customer_id          VARCHAR(100),

    created_at                  TIMESTAMPTZ,
    updated_at                  TIMESTAMPTZ,

    signup_channel              VARCHAR(50),

    square_sync_status          VARCHAR(50),
    square_synced_at            TIMESTAMPTZ,
    square_sync_error           TEXT
);


-- =========================================================
-- 3. Customer Addresses
-- =========================================================

CREATE TABLE IF NOT EXISTS raw_online.customer_addresses (
    id                          VARCHAR(100),
    customer_id                 VARCHAR(100),

    label                       VARCHAR(50),

    address_line1               VARCHAR(255),
    address_line2               VARCHAR(255),

    city                        VARCHAR(100),
    province                    VARCHAR(50),
    postal_code                 VARCHAR(20),
    country                     VARCHAR(50),

    is_default                  BOOLEAN,

    created_at                  TIMESTAMPTZ,

    square_customer_id          VARCHAR(100)
);


-- =========================================================
-- 4. Orders
-- =========================================================

CREATE TABLE IF NOT EXISTS raw_online.orders (
    id                          VARCHAR(100),
    order_id                    VARCHAR(100),

    channel                     VARCHAR(50),
    store_id                    VARCHAR(100),
    customer_id                 VARCHAR(100),
    customer_type               VARCHAR(50),

    contact_first_name          VARCHAR(100),
    contact_last_name           VARCHAR(100),
    contact_email               VARCHAR(255),
    contact_phone               VARCHAR(50),

    shipping_address_line1      VARCHAR(255),
    shipping_address_line2      VARCHAR(255),
    shipping_city               VARCHAR(100),
    shipping_province           VARCHAR(50),
    shipping_postal_code        VARCHAR(20),
    shipping_country            VARCHAR(50),

    order_status                VARCHAR(50),

    subtotal                    NUMERIC(12, 2),

    discount_type               VARCHAR(50),
    discount_amount             NUMERIC(12, 2),
    discount_reason             TEXT,

    tax_rate                    NUMERIC(8, 4),
    tax_amount                  NUMERIC(12, 2),

    shipping_amount             NUMERIC(12, 2),
    total_amount                NUMERIC(12, 2),

    payment_method              VARCHAR(50),
    item_count                  INTEGER,

    created_at                  TIMESTAMPTZ,
    completed_at                TIMESTAMPTZ,

    square_order_id             VARCHAR(100),
    square_customer_id          VARCHAR(100),
    square_location_id          VARCHAR(100),

    square_sync_status          VARCHAR(50),
    square_synced_at            TIMESTAMPTZ,
    square_sync_error           TEXT
);


-- =========================================================
-- 5. Order Items
-- =========================================================

CREATE TABLE IF NOT EXISTS raw_online.order_items (
    id                          VARCHAR(100),
    order_id                    VARCHAR(100),

    store_id                    VARCHAR(100),
    product_id                  VARCHAR(100),

    sku                         VARCHAR(100),
    product_name                VARCHAR(255),
    category                    VARCHAR(100),

    quantity                    INTEGER,

    unit_price                  NUMERIC(12, 2),
    discount_amount             NUMERIC(12, 2),
    line_total                  NUMERIC(12, 2),

    square_catalog_object_id    VARCHAR(100),

    created_at                  TIMESTAMPTZ,

    square_line_item_uid        VARCHAR(100)
);