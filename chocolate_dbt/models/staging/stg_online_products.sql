
{{ config(materialized='view') }}

with source as (

    select *
    from {{ source('online', 'products') }}

),

cleaned as (

    select
        -- Identifiers
        nullif(trim(id), '') as source_record_id,
        nullif(trim(product_id), '') as product_id,

        -- Product attributes
        nullif(trim(sku), '') as sku,
        nullif(trim(product_name), '') as product_name,
        nullif(trim(category), '') as category,
        nullif(trim(description), '') as description,
        nullif(trim(image_key), '') as image_key,

        -- Price in CAD
        price,

        -- Product flags
        is_best_seller,
        active_status,

        -- Square integration
        nullif(trim(square_catalog_object_id), '')
            as square_catalog_object_id,

        upper(nullif(trim(square_sync_status), ''))
            as square_sync_status,

        square_synced_at,
        square_sync_error,

        -- Timestamps
        created_at,
        updated_at,

        -- Pipeline metadata
        ingested_at,
        orchestrator,
        pipeline_run_id

    from source

)

select *
from cleaned
