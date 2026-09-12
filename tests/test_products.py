from src.config.paths import RAW_DATA_DIR, PROCESSED_DATA_DIR
from src.extract.load_csv import load_csv
from src.square.catalog import search_product_by_sku
from src.transform.products import transform_product

products_path = RAW_DATA_DIR / "products_export.csv"

df = load_csv(products_path)

print(df.head())

# 첫 번째 상품 한 건만 DataFrame으로 가져오기
product_df = df.iloc[[0]]

print(product_df)

sku = product_df["sku"].iloc[0]
print("sku >>>>", sku)
existing_product = search_product_by_sku(sku)

if not existing_product:
    print(f"[NEW] {sku}")

    square_product = transform_product(product_df)
    print(square_product)

