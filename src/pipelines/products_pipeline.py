# products_pipeline.py
# 상품 데이터 처리의 전체 흐름을 관리하는 역할
# CSV load 함수 load_csv()를 호출해 DataFrame을 가져오고,
# transforms/products.py에 전달하여 Square API 형식으로 변환한 뒤,
# 변환된 데이터를 Square API 전송 단계로 전달한다.
from src.config.paths import RAW_DATA_DIR
from src.extract.load_csv import load_csv
from src.square.catalog import search_product_by_sku
from src.transform.products import transform_product

products_path = RAW_DATA_DIR / "products_export.csv"

df = load_csv(products_path)

# 처리 현황 카운트
total_count = len(df)
existing_count = 0
new_count = 0

print(f"Total products to check: {total_count}")
print("-" * 50)

for _, row in df.iterrows():
    sku = row["sku"]

    existing_product = search_product_by_sku(sku)

    if existing_product:
        existing_count += 1
        print(f"[EXISTS] {sku}")
        continue

    #.existing_product == False면,
    # 해당 상품을 우리가 iterrows 했기때문에, Pandas Series 형태로 바뀌었잖아 그래서
    # 다시 DataFrame으로 만든 후 (왜나면 transform_product(dataframe) 호출할때 변수를 DF으로 넘기니까),
    # 세로형식으로 만들어진 DF을 Transpose(전치)해서 가로로 만든 후 호출.
    if not existing_product:
        new_count += 1
        print(f"[NEW] {sku}")

        product_df = row.to_frame().T
        product = transform_product(product_df)

print("-" * 50)
print("Product Processing Summary")
print(f"Total checked : {total_count}")
print(f"Already exists: {existing_count}")
print(f"New products  : {new_count}")







