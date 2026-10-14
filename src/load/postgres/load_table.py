import pandas as pd
from sqlalchemy.engine import Engine


def load_dataframe_to_postgres(
    df: pd.DataFrame,
    table_name: str,
    engine: Engine,
    if_exists: str = "replace"
) -> None:
    """
    Pandas DataFrame을 PostgreSQL 테이블로 적재
    """

    df.to_sql(
        name=table_name,
        con=engine,
        if_exists=if_exists,
        index=False
    )

    print(
        f"[SUCCESS] {table_name} table loaded "
        f"({len(df)} rows)"
    )