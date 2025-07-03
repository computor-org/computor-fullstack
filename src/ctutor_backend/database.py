import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, Session

POSTGRES_URL = os.environ.get("POSTGRES_URL")
POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGRES_DB = os.environ.get("POSTGRES_DB")

_database_options = {
    "pool_pre_ping": True,
    "pool_size": 10,
    "max_overflow": 5,
    "pool_timeout": 30,
    "pool_recycle": 300
}

_engine = create_engine(f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_URL}/{POSTGRES_DB}", **_database_options)
_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

def get_db() -> Generator[Session, None, None]:

    db = _SessionLocal()

    try:
        yield db
    except OperationalError as e:
        print("Database connection failed")
        db.rollback()
        raise
    finally:
        db.close()
