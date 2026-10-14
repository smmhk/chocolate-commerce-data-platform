-- =========================================================
-- Online Ingestion Validation
-- =========================================================


-- =========================================================
-- 1. Products
-- =========================================================

SELECT COUNT(*) AS total_products
FROM products;

SELECT *
FROM products
WHERE id IS NULL;

SELECT
    id,
    COUNT(*) AS duplicate_count
FROM products
GROUP BY id
HAVING COUNT(*) > 1;


-- =========================================================
-- 2. Customers
-- =========================================================

SELECT COUNT(*) AS total_customers
FROM customers;

SELECT *
FROM customers
WHERE id IS NULL;

SELECT
    id,
    COUNT(*) AS duplicate_count
FROM customers
GROUP BY id
HAVING COUNT(*) > 1;

SELECT
    signup_channel,
    COUNT(*) AS customer_count
FROM customers
GROUP BY signup_channel;


-- =========================================================
-- 3. Customer Addresses
-- =========================================================

SELECT COUNT(*) AS total_customer_addresses
FROM customer_addresses;

SELECT *
FROM customer_addresses
WHERE id IS NULL;

SELECT
    id,
    COUNT(*) AS duplicate_count
FROM customer_addresses
GROUP BY id
HAVING COUNT(*) > 1;

SELECT *
FROM customer_addresses
WHERE customer_id IS NULL;

SELECT ca.*
FROM customer_addresses ca
LEFT JOIN customers c
    ON ca.customer_id = c.id
WHERE c.id IS NULL;


-- =========================================================
-- 4. Orders
-- =========================================================

SELECT COUNT(*) AS total_orders
FROM orders;

SELECT *
FROM orders
WHERE id IS NULL;

SELECT
    id,
    COUNT(*) AS duplicate_count
FROM orders
GROUP BY id
HAVING COUNT(*) > 1;

SELECT
    channel,
    COUNT(*) AS order_count
FROM orders
GROUP BY channel;

SELECT *
FROM orders
WHERE UPPER(TRIM(channel)) <> 'ONLINE';


-- =========================================================
-- 5. Order Items
-- =========================================================

SELECT COUNT(*) AS total_order_items
FROM order_items;

SELECT *
FROM order_items
WHERE id IS NULL;

SELECT
    id,
    COUNT(*) AS duplicate_count
FROM order_items
GROUP BY id
HAVING COUNT(*) > 1;

SELECT *
FROM order_items
WHERE order_id IS NULL;

SELECT oi.*
FROM order_items oi
LEFT JOIN orders o
    ON oi.order_id = o.id
WHERE o.id IS NULL;