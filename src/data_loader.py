import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from .config import DATA_DIR, DATABASE_URL


TABLE_FILES = {
    "customers": "customers.csv",
    "products": "products.csv",
    "stores": "stores.csv",
    "calendar": "calendar.csv",
    "sales": "sales.csv",
}


DDL = {
    "customers": """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            age INTEGER,
            gender TEXT,
            loyalty_member INTEGER,
            join_date DATE
        )
    """,
    "products": """
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            product_name TEXT,
            brand TEXT,
            category TEXT,
            cocoa_percent INTEGER,
            weight_g INTEGER
        )
    """,
    "stores": """
        CREATE TABLE IF NOT EXISTS stores (
            store_id TEXT PRIMARY KEY,
            store_name TEXT,
            city TEXT,
            country TEXT,
            store_type TEXT
        )
    """,
    "calendar": """
        CREATE TABLE IF NOT EXISTS calendar (
            date DATE PRIMARY KEY,
            year INTEGER,
            month INTEGER,
            day INTEGER,
            week INTEGER,
            day_of_week INTEGER
        )
    """,
    "sales": """
        CREATE TABLE IF NOT EXISTS sales (
            order_id TEXT PRIMARY KEY,
            order_date DATE,
            product_id TEXT,
            store_id TEXT,
            customer_id TEXT,
            quantity INTEGER,
            unit_price NUMERIC,
            discount NUMERIC,
            revenue NUMERIC,
            cost NUMERIC,
            profit NUMERIC
        )
    """,
}


INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_id)",
    "CREATE INDEX IF NOT EXISTS idx_sales_product ON sales(product_id)",
    "CREATE INDEX IF NOT EXISTS idx_sales_store ON sales(store_id)",
    "CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(order_date)",
]


def get_engine() -> Engine:
    return create_engine(DATABASE_URL, pool_pre_ping=True)


def database_ready(engine: Engine | None = None) -> bool:
    engine = engine or get_engine()
    with engine.connect() as conn:
        found = conn.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                """
            )
        ).fetchall()
    return {row[0] for row in found}.issuperset(TABLE_FILES)


def create_tables(engine: Engine | None = None) -> None:
    engine = engine or get_engine()
    with engine.begin() as conn:
        for ddl in DDL.values():
            conn.execute(text(ddl))
        for statement in INDEXES:
            conn.execute(text(statement))


def load_csv_data(engine: Engine | None = None) -> None:
    engine = engine or get_engine()
    create_tables(engine)
    with engine.begin() as conn:
        for table in ["sales", "customers", "products", "stores", "calendar"]:
            conn.execute(text(f"TRUNCATE TABLE {table}"))

    for table, file_name in TABLE_FILES.items():
        csv_path = DATA_DIR / file_name
        if not csv_path.exists():
            raise FileNotFoundError(f"Missing dataset file: {csv_path}")

        if table == "sales":
            for chunk in pd.read_csv(csv_path, chunksize=3_000):
                chunk.to_sql(table, engine, if_exists="append", index=False, method="multi")
        else:
            df = pd.read_csv(csv_path)
            df.to_sql(table, engine, if_exists="append", index=False, method="multi")


def ensure_database() -> None:
    engine = get_engine()
    if not database_ready(engine):
        load_csv_data(engine)


def table_counts(engine: Engine | None = None) -> dict[str, int]:
    engine = engine or get_engine()
    with engine.connect() as conn:
        return {
            table: conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
            for table in TABLE_FILES
        }


def table_columns(engine: Engine | None = None) -> dict[str, list[str]]:
    engine = engine or get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
                """
            )
        ).fetchall()
    columns: dict[str, list[str]] = {table: [] for table in TABLE_FILES}
    for table, column in rows:
        if table in columns:
            columns[table].append(column)
    return columns
