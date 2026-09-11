import pandas as pd


# CSV 파일 읽기 공통코드
def load_csv(file_path) -> pd.DataFrame:
    df = pd.read_csv(file_path, sep=";")
    return df
