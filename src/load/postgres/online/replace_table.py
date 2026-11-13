import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine


ALLOWED_TABLES = {
    "products",
    "customers",
    "customer_addresses",
    "orders",
    "order_items",
}


def load_dataframe_to_postgres(
    df: pd.DataFrame,
    table_name: str,
    engine: Engine,
) -> None:
    """raw_online 테이블의 기존 데이터를 새 데이터로 교체한다."""

    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Unsupported table: {table_name}")

    # 정상 종료 시 커밋, 오류 발생 시 이 테이블의 변경 롤백
    with engine.begin() as connection:
        # 테이블 구조는 유지하고 기존 행만 삭제
        connection.execute(
            text(f'DELETE FROM raw_online."{table_name}"')
        )

        # 같은 연결에서 새 데이터 추가
        df.to_sql(
            name=table_name,
            schema="raw_online",
            con=connection,
            if_exists="append",
            index=False,
        )

    print(
        f"[SUCCESS] raw_online.{table_name} loaded "
        f"({len(df)} rows)"
    )