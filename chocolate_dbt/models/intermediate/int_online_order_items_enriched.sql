
{{ config(materialized='view') }}

with order_items as (

    select *
    from {{ ref('stg_online_order_items') }}

),

orders as (

    select *
    from {{ ref('stg_online_orders') }}

),

products as (

    select *
    from {{ ref('stg_online_products') }}

),

enriched as (

    select
        -- Grain: one row per order line item
        oi.source_record_id as order_item_id,
        oi.order_id,
        oi.product_id,
        o.customer_id,

        -- Order context
        o.channel,
        o.order_status,
        o.order_date,
        o.order_created_at,

        case
            when o.order_status = 'COMPLETED'
                then true
            else false
        end as is_completed_order,

        -- Product attributes
        oi.sku,
        oi.product_name as product_name_at_order,
        oi.category as category_at_order,
        p.product_name as current_product_name,
        p.category as current_product_category,

        -- Financial details (CAD)
        oi.quantity,
        oi.unit_price,
        oi.discount_amount,
        oi.line_total,

        -- Current catalog context
        p.price as current_catalog_price,
        p.active_status as current_product_active

    from order_items oi

    left join orders o
        on oi.order_id = o.order_id

    left join products p
        on oi.product_id = p.product_id

)

select *
from enriched
