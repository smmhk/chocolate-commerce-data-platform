
{{ config(materialized='view') }}

with source as (

    select *
    from {{ source('online', 'orders') }}

),

cleaned as (

    select
        -- Identifiers
        nullif(trim(id), '') as source_record_id,
        nullif(trim(order_id), '') as order_id,
        nullif(trim(customer_id), '') as customer_id,
        nullif(trim(store_id), '') as store_id,

        -- Channel and status
        upper(nullif(trim(channel), '')) as channel,
        upper(nullif(trim(customer_type), '')) as customer_type,
        upper(nullif(trim(order_status), '')) as order_status,

        -- Financial amounts (CAD)
        subtotal,
        discount_amount,
        tax_amount,
        shipping_amount,
        total_amount,

        -- Order details
        item_count,

        -- Timestamps
        created_at as order_created_at,
        completed_at as order_completed_at,

        date(
            created_at,
            'America/Vancouver'
        ) as order_date,

        -- Square integration
        nullif(trim(square_order_id), '') as square_order_id,
        nullif(trim(square_customer_id), '') as square_customer_id,
        nullif(trim(square_location_id), '') as square_location_id,

        -- Pipeline metadata
        ingested_at,
        orchestrator,
        pipeline_run_id

    from source

)

select *
from cleaned
