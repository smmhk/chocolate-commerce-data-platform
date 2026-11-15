from pathlib import Path


# 프로젝트 최상위 폴더
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 공통 데이터 경로
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

import os
from datetime import date


def get_online_source_dir():
    source_date = os.environ.get("SOURCE_DATE")

    # 날짜를 지정하지 않은 기존 실행은 기존 경로 사용
    if source_date is None:
        return RAW_DATA_DIR

    parsed = date.fromisoformat(source_date)
    if parsed.isoformat() != source_date:
        raise ValueError("SOURCE_DATE must use YYYY-MM-DD format")

    return RAW_DATA_DIR / "simulated_commerce" / source_date