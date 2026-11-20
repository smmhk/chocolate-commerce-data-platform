
{{ config(materialized='view') }}

with source as (

    select *
    from {{ source('online', 'customers') }}

),

cleaned as (

    select
        -- Identifiers
        nullif(trim(id), '') as customer_id,
        nullif(trim(customer_number), '') as customer_number,
        nullif(trim(user_id), '') as user_id,

        -- Customer information
        lower(nullif(trim(email), '')) as email,
        nullif(trim(first_name), '') as first_name,
        nullif(trim(last_name), '') as last_name,
        nullif(trim(phone), '') as phone,

        -- Customer classification
        upper(nullif(trim(customer_type), '')) as customer_type,
        upper(nullif(trim(signup_channel), '')) as signup_channel,

        -- Square integration
        nullif(trim(square_customer_id), '')
            as square_customer_id,

        upper(nullif(trim(square_sync_status), ''))
            as square_sync_status,

        square_synced_at,
        square_sync_error,

        -- Timestamps
        created_at as customer_created_at,
        updated_at as customer_updated_at,

        -- Pipeline metadata
        ingested_at,
        orchestrator,
        pipeline_run_id

    from source

)

select *
from cleaned
