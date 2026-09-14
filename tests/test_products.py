import pandas as pd

from src.config.paths import RAW_DATA_DIR, PROCESSED_DATA_DIR
from src.extract.load_csv import load_csv
from src.square.catalog import search_product_by_sku, delete_product
from src.transform.products import transform_product

pd.set_option("display.max_columns", None)   # 모든 컬럼 출력
pd.set_option("display.max_rows", None)      # 모든 행 출력
pd.set_option("display.max_colwidth", None)  # 긴 문자열도 생략하지 않음
pd.set_option("display.width", None)         # 화면 너비에 따른 컬럼 생략 방지

products_path = RAW_DATA_DIR / "products_export.csv"

df = load_csv(products_path)

print(df.head())

# 첫 번째 상품 한 건만 DataFrame으로 가져오기
product_df = df.iloc[[0]]
print("TEST TARGET PRODUCT DF : ", product_df)

sku = product_df["sku"].iloc[0]
print("targeted sku >>>>", sku)
existing_product = search_product_by_sku(sku)
print("existing_product T or F >>>>", existing_product)

if not existing_product:
    print(f" Target [NEW] info (sku) : {sku}")

    square_product = transform_product(product_df)
    print(square_product)