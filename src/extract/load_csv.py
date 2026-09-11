import pandas as pd

def load_csv(file_path) -> pd.DataFrame:
    df = pd.read_csv(file_path, sep=";")
    return df
