import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from core.config import settings

# ──────────────────────────────────────────────
# Build connection kwargs — Supabase needs SSL
# ──────────────────────────────────────────────
DATABASE_URL = settings.DATABASE_URL

# Supabase / most hosted Postgres requires SSL.
# If the URL doesn't already include sslmode, add it.
if "supabase" in DATABASE_URL or "pooler.supabase" in DATABASE_URL:
    if "sslmode" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL + "?sslmode=require"
    connect_args = {"sslmode": "require"}
    # Supabase transaction-mode pooler: use NullPool to avoid
    # "prepared statement already exists" errors
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        connect_args=connect_args,
    )
else:
    # Local / Railway / regular Postgres
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables():
    """Create all tables; log success or failure — never crash startup."""
    try:
        from database import models  # noqa: F401  — registers all models
        Base.metadata.create_all(bind=engine)
        # Quick connectivity check
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[DB] ✅ Tables created and connection verified.")
    except Exception as e:
        print(f"[DB] ❌ Startup DB error: {e}")
        print("[DB] ⚠️  Check DATABASE_URL environment variable in Render settings.")
        # We do NOT re-raise — let the app start so /health still works.
