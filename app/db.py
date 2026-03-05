import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "flaky_gate")

DB_USER = "postgres"
DB_PASSWORD = "postgres"

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

GLOBAL_SESSION = SessionLocal()


def get_db():
    return GLOBAL_SESSION