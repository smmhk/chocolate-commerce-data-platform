
{{ config(materialized='view') }}

with source as (

    select *
    from {{ source('online', 'order_items') }}

),

cleaned as (

    select
        -- Identifiers
        nullif(trim(id), '') as source_record_id,
        nullif(trim(order_id), '') as order_id,
        nullif(trim(store_id), '') as store_id,
        nullif(trim(product_id), '') as product_id,

        -- Product details at time of order
        nullif(trim(sku), '') as sku,
        nullif(trim(product_name), '') as product_name,
        nullif(trim(category), '') as category,

        -- Quantity and monetary values (CAD)
        quantity,
        unit_price,
        discount_amount,
        line_total,

        -- Square integration
        nullif(trim(square_catalog_object_id), '')
            as square_catalog_object_id,

        nullif(trim(square_line_item_uid), '')
            as square_line_item_uid,

        -- Timestamps
        created_at as line_item_created_at,

        -- Pipeline metadata
        ingested_at,
        orchestrator,
        pipeline_run_id

    from source

)

select *
from cleaned
