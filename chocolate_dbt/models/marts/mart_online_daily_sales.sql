
{{ config(materialized='view') }}

select
    order_date,

    count(*) as total_orders,

    sum(total_amount) as total_order_amount_cad

from {{ ref('stg_online_orders') }}

where order_status = 'COMPLETED'

group by order_date
order by order_date