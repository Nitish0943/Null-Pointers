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
    Safe no-downtime migration: adds new columns to existing DB if they don't exist.
    Both ML and RCA fields are handled here.
    """
    migrations = [
        ("anomaly_flag",    "BOOLEAN DEFAULT 0"),
        ("anomaly_score",   "FLOAT DEFAULT 0.0"),
        ("rca_root_cause",  "TEXT DEFAULT 'No Fault Detected'"),
        ("rca_confidence",  "FLOAT DEFAULT 0.0"),
        ("rca_severity",    "TEXT DEFAULT 'LOW'"),
        ("rca_reasoning",   "TEXT DEFAULT '[]'"),
        # Agent columns — 4-agent integration
        ("llm_explanation", "TEXT DEFAULT NULL"),
        ("alert_state",     "TEXT DEFAULT 'CLEAR'"),
        ("machine_voice",   "TEXT DEFAULT NULL"),
    ]
    with engine.connect() as conn:
        # Migrate analysis_results
        for col_name, col_def in migrations:
            try:
                conn.execute(text(f"ALTER TABLE analysis_results ADD COLUMN {col_name} {col_def}"))
                print(f"[DB Migration] + analysis_results column: {col_name}")
            except Exception: pass
        
        # Migrate source column specifically for both tables
        for table in ["telemetry_data", "analysis_results"]:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN source TEXT DEFAULT 'simulated'"))
                print(f"[DB Migration] + {table} column: source")
            except Exception: pass
            
        conn.commit()
    
    # Migrate maintenance_tickets
    maintenance_migrations = [
        ("severity",          "TEXT DEFAULT 'LOW'"),
        ("loss_estimate_inr", "FLOAT DEFAULT 0.0"),
    ]
    with engine.connect() as conn:
        for col_name, col_def in maintenance_migrations:
            try:
                conn.execute(text(f"ALTER TABLE maintenance_tickets ADD COLUMN {col_name} {col_def}"))
                print(f"[DB Migration] + maintenance_tickets column: {col_name}")
            except Exception: pass
        conn.commit()

    print("[DB Migration] Schema is up to date.")


