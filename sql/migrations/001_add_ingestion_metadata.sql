ALTER TABLE raw_online.products
    ADD COLUMN IF NOT EXISTS ingested_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS orchestrator VARCHAR(50),
    ADD COLUMN IF NOT EXISTS pipeline_run_id VARCHAR(100);

ALTER TABLE raw_online.customers
    ADD COLUMN IF NOT EXISTS ingested_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS orchestrator VARCHAR(50),
    ADD COLUMN IF NOT EXISTS pipeline_run_id VARCHAR(100);

ALTER TABLE raw_online.customer_addresses
    ADD COLUMN IF NOT EXISTS ingested_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS orchestrator VARCHAR(50),
    ADD COLUMN IF NOT EXISTS pipeline_run_id VARCHAR(100);

ALTER TABLE raw_online.orders
    ADD COLUMN IF NOT EXISTS ingested_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS orchestrator VARCHAR(50),
    ADD COLUMN IF NOT EXISTS pipeline_run_id VARCHAR(100);

ALTER TABLE raw_online.order_items
    ADD COLUMN IF NOT EXISTS ingested_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS orchestrator VARCHAR(50),
    ADD COLUMN IF NOT EXISTS pipeline_run_id VARCHAR(100);