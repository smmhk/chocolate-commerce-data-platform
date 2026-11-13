{{ config(materialized='view') }}

select
    order_id,
    channel,
    nullif(trim(order_status), '') as order_status,
    total_amount,
    created_at as order_created_at
from {{ source('online', 'orders') }}