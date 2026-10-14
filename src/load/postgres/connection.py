from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

def get_postgres_engine() -> Engine:
    """
    PostgreSQL SQLAlchemy engine 생성
    """

    user = "chocolate"
    password = "chocolate123"
    host = "localhost"
    port = 5432
    database = "chocolate_db"

    connection_url = (
        f"postgresql+psycopg2://{user}:{password}"
        f"@{host}:{port}/{database}"
    )

    engine = create_engine(connection_url)

    return engine