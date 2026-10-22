# =========================================================
# Transform
# =========================================================

def filter_online_data(source_data):
    """원본 데이터에서 온라인 고객·주문과 관련 데이터를 선별한다."""

    # 원본 DataFrame 꺼내기
    products_df = source_data["products"]
    customers_df = source_data["customers"]
    addresses_df = source_data["customer_addresses"]
    orders_df = source_data["orders"]
    order_items_df = source_data["order_items"]

    # =====================================================
    # 1. Products
    # =====================================================

    # 상품은 기존 코드와 동일하게 전체 사용
    online_products_df = products_df

    # =====================================================
    # 2. Customers
    # =====================================================

    # ONLINE을 통해 가입한 고객만 추출
    online_customers_df = customers_df[
        customers_df["signup_channel"]
        .str.strip()
        .str.upper()
        == "ONLINE"
    ].copy()

    # =====================================================
    # 3. Customer Addresses
    # =====================================================

    # ONLINE 고객들의 ID
    online_customer_ids = online_customers_df["id"]

    # 해당 고객의 주소만 추출
    online_addresses_df = addresses_df[
        addresses_df["customer_id"].isin(
            online_customer_ids
        )
    ].copy()

    # =====================================================
    # 4. Orders
    # =====================================================

    # ONLINE 주문만 추출
    online_orders_df = orders_df[
        orders_df["channel"]
        .str.strip()
        .str.upper()
        == "ONLINE"
    ].copy()

    # =====================================================
    # 5. Order Items
    # =====================================================

    # ONLINE 주문의 비즈니스 주문번호
    # orders.order_id ↔ order_items.order_id
    online_order_ids = online_orders_df["order_id"]

    # 해당 주문에 포함된 주문상품만 추출
    online_order_items_df = order_items_df[
        order_items_df["order_id"].isin(
            online_order_ids
        )
    ].copy()

    # =====================================================
    # Return
    # =====================================================

    online_data = {
        "products": online_products_df,
        "customers": online_customers_df,
        "customer_addresses": online_addresses_df,
        "orders": online_orders_df,
        "order_items": online_order_items_df,
    }

    for table_name, df in online_data.items():
        print(
            f"[TRANSFORM] {table_name} rows: {len(df)}"
        )

    return online_data