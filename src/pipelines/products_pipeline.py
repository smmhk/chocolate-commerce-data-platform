# products_pipeline.py
# 상품 데이터 처리의 전체 흐름을 관리하는 역할
# CSV load 함수 load_csv()를 호출해 DataFrame을 가져오고,
# transforms/products.py에 전달하여 Square API 형식으로 변환한 뒤,
# 변환된 데이터를 Square API 전송 단계로 전달한다.
from src.config.paths import RAW_DATA_DIR
from src.extract.load_csv import load_csv
from src.transform.products import transform_products

products_path = RAW_DATA_DIR / "products_export.csv"

df = load_csv(products_path)

transform_products(df)


