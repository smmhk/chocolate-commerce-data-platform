from pathlib import Path


# 프로젝트 최상위 폴더
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 공통 데이터 경로
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"