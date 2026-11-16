
{{ config(materialized='view') }}

with source as (

    select *
    from {{ source('online', 'customer_addresses') }}

),

cleaned as (

    select
        -- Identifiers
        nullif(trim(id), '') as source_record_id,
        nullif(trim(customer_id), '') as customer_id,

        -- Address details
        nullif(trim(label), '') as address_label,
        nullif(trim(address_line1), '') as address_line1,
        nullif(trim(address_line2), '') as address_line2,
        nullif(trim(city), '') as city,

        upper(nullif(trim(province), '')) as province,
        upper(nullif(trim(postal_code), '')) as postal_code,
        upper(nullif(trim(country), '')) as country,

        -- Address flags
        is_default,

        -- Square integration
        nullif(trim(square_customer_id), '')
            as square_customer_id,

        -- Timestamps
        created_at as address_created_at,

        -- Pipeline metadata
        ingested_at,
        orchestrator,
        pipeline_run_id

    from source

)

select *
from cleaned
