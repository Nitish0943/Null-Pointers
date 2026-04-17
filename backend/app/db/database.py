from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from typing import Generator

DATABASE_URL = "sqlite:///./backend.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def migrate_db():
    """
    Safe no-downtime migration: adds new ML columns to existing DB if they don't exist.
    This avoids needing to delete and recreate the database.
    """
    with engine.connect() as conn:
        # Check and add anomaly_flag column
        try:
            conn.execute(text("ALTER TABLE analysis_results ADD COLUMN anomaly_flag BOOLEAN DEFAULT 0"))
            print("[DB Migration] ✓ Added column: anomaly_flag")
        except Exception:
            pass  # Column already exists

        # Check and add anomaly_score column
        try:
            conn.execute(text("ALTER TABLE analysis_results ADD COLUMN anomaly_score FLOAT DEFAULT 0.0"))
            print("[DB Migration] ✓ Added column: anomaly_score")
        except Exception:
            pass  # Column already exists

        conn.commit()

