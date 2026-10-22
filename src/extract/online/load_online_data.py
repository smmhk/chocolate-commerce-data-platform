from pathlib import Path

from src.extract.load_csv import load_csv


# =========================================================
# File Paths
# =========================================================

# 현재 파일: src/extract/online/load_online_data.py
# parents[3]: 프로젝트 루트 폴더
BASE_DIR = Path(__file__).resolve().parents[3]
RAW_DIR = BASE_DIR / "data" / "raw"

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
    """온라인 파이프라인에 사용할 원본 CSV 5개를 읽는다."""

    source_data = {}

    for table_name, filename in CSV_FILES.items():
        file_path = RAW_DIR / filename

        df = load_csv(file_path)

        print(
            f"[EXTRACT] {table_name} rows: {len(df)}"
        )

        source_data[table_name] = df

    return source_data