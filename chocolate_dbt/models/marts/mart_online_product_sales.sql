
{{ config(materialized='view') }}

select
    product_id,

    max(product_name_at_order) as product_name,
    max(category_at_order) as category,

    sum(quantity) as units_sold,

    count(distinct order_id) as order_count,

    sum(line_total) as item_amount_cad

from {{ ref('int_online_order_items_enriched') }}

where is_completed_order = true

group by product_id
