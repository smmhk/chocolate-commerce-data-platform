import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, URL


load_dotenv()


def get_postgres_engine() -> Engine:
    """환경 변수로 PostgreSQL 연결 정보를 읽어 엔진을 생성한다."""

    password = os.getenv("CHOCOLATE_DB_PASSWORD")

    if not password:
        raise ValueError(
            "CHOCOLATE_DB_PASSWORD 환경 변수가 필요합니다."
        )

    connection_url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("CHOCOLATE_DB_USER", "chocolate"),
        password=password,
        host=os.getenv("CHOCOLATE_DB_HOST", "localhost"),
        port=int(os.getenv("CHOCOLATE_DB_PORT", "5432")),
        database=os.getenv("CHOCOLATE_DB_NAME", "chocolate_db"),
    )

    return create_engine(connection_url)