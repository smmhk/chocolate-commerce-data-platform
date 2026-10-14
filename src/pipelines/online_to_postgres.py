from pathlib import Path

from src.extract.load_csv import load_csv
from src.load.postgres.connection import get_postgres_engine
from src.load.postgres.load_table import load_dataframe_to_postgres


# =========================================================
# File Paths
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

PRODUCTS_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "products_export.csv"
)

CUSTOMERS_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "customers_export.csv"
)

CUSTOMER_ADDRESSES_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "customer_addresses_export.csv"
)

ORDERS_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "orders_export.csv"
)

ORDER_ITEMS_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "order_items_export.csv"
)


# =========================================================
# Online → PostgreSQL Pipeline
# =========================================================

def run():

    print("[START] Online → PostgreSQL ingestion")

    # PostgreSQL 연결
    engine = get_postgres_engine()


    # =====================================================
    # 1. Products
    # =====================================================

    products_df = load_csv(PRODUCTS_PATH)

    print(f"[INFO] products rows: {len(products_df)}")

    load_dataframe_to_postgres(
        df=products_df,
        table_name="products",
        engine=engine,
        if_exists="replace"
    )


    # =====================================================
    # 2. Customers
    # =====================================================

    customers_df = load_csv(CUSTOMERS_PATH)

    print(f"[INFO] total customers rows: {len(customers_df)}")

    # ONLINE을 통해 가입한 고객만 추출
    online_customers_df = customers_df[
        customers_df["signup_channel"].str.strip().str.upper() == "ONLINE"
        ].copy()

    print(
        f"[INFO] online customers rows: "
        f"{len(online_customers_df)}"
    )

    load_dataframe_to_postgres(
        df=online_customers_df,
        table_name="customers",
        engine=engine,
        if_exists="replace"
    )


    # =====================================================
    # 3. Customer Addresses
    # =====================================================

    addresses_df = load_csv(CUSTOMER_ADDRESSES_PATH)

    print(
        f"[INFO] total customer addresses rows: "
        f"{len(addresses_df)}"
    )

    # ONLINE 고객들의 ID만 가져오기
    online_customer_ids = online_customers_df["id"]

    # customer_id가 ONLINE 고객 ID에 포함되는 주소만 추출
    online_addresses_df = addresses_df[
        addresses_df["customer_id"].isin(online_customer_ids)
    ].copy()

    print(
        f"[INFO] online customer addresses rows: "
        f"{len(online_addresses_df)}"
    )

    load_dataframe_to_postgres(
        df=online_addresses_df,
        table_name="customer_addresses",
        engine=engine,
        if_exists="replace"
    )

    # =====================================================
    # 4. Orders
    # =====================================================

    orders_df = load_csv(ORDERS_PATH)

    print(
        f"[INFO] total orders rows: "
        f"{len(orders_df)}"
    )

    # ONLINE 주문만 추출
    online_orders_df = orders_df[
        orders_df["channel"].str.strip().str.upper() == "ONLINE"
        ].copy()

    print(
        f"[INFO] online orders rows: "
        f"{len(online_orders_df)}"
    )

    load_dataframe_to_postgres(
        df=online_orders_df,
        table_name="orders",
        engine=engine,
        if_exists="replace"
    )

    # =====================================================
    # 5. Order Items
    # =====================================================

    order_items_df = load_csv(ORDER_ITEMS_PATH)

    print(
        f"[INFO] total order items rows: "
        f"{len(order_items_df)}"
    )

    # ONLINE 주문 ID 목록
    online_order_ids = online_orders_df["id"]

    # ONLINE 주문에 포함된 주문상품만 추출
    online_order_items_df = order_items_df[
        order_items_df["order_id"].isin(online_order_ids)
    ].copy()

    print(
        f"[INFO] online order items rows: "
        f"{len(online_order_items_df)}"
    )

    load_dataframe_to_postgres(
        df=online_order_items_df,
        table_name="order_items",
        engine=engine,
        if_exists="replace"
    )


    # =====================================================
    # Done
    # =====================================================

    print("[DONE] Online → PostgreSQL ingestion")


# =========================================================
# Run Pipeline
# =========================================================

if __name__ == "__main__":
    run()