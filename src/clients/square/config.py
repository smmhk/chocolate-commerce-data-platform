# Square URL / Token / headers 같은 공통 설정
import os

from dotenv import load_dotenv

load_dotenv() #.env 파일에 저장해둔 환경변수 Python이 사용할 수 있도록 불러오는 함수

access_token = os.getenv("SQUARE_ACCESS_TOKEN")


""" ex) SKU 중복확인용 Square search-catalog-items API 조회
curl https://connect.squareupsandbox.com/v2/catalog/search-catalog-items \
  -X POST \
  -H 'Square-Version: 2026-08-19' \
  -H 'Authorization: Bearer [token]' \
  -H 'Content-Type: application/json' \
  -d '{
    "text_filter": "CCF-SEA-001"
  }'"""

headers = {
    "Square-Version": "2026-08-19",
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}



