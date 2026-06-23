"""SQLAlchemy engine, session and Base."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from . import config

_url = config.DATABASE_URL
connect_args = {}
if _url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif "+pg8000" in _url:
    # Managed Postgres (Neon, etc.) requires TLS. pg8000 takes an ssl_context and
    # doesn't understand libpq query params (sslmode/channel_binding) — strip them.
    import ssl
    if "?" in _url:
        _url = _url.split("?", 1)[0]
    connect_args = {"ssl_context": ssl.create_default_context()}

engine = create_engine(_url, connect_args=connect_args, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
