from src.config.paths import get_online_source_dir
from src.extract.csv_reader import load_csv


CSV_FILES = {
    "products": "products_export.csv",
    "customers": "customers_export.csv",
    "customer_addresses": "customer_addresses_export.csv",
    "orders": "orders_export.csv",
    "order_items": "order_items_export.csv",
}


# =========================================================
# Extract
# =========================================================

def load_online_data():
    source_dir = get_online_source_dir()
    source_data = {}

    for table_name, filename in CSV_FILES.items():
        file_path = source_dir / filename
        df = load_csv(file_path)
        source_data[table_name] = df

    return source_data