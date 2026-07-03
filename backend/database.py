import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./monitor.db")

# check_same_thread=False: SQLite + multiple asyncio monitor tasks touching
# the same file. Each request/task still gets its own Session, so this is safe.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# --- ADDED THIS FUNCTION ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()