import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

logger = logging.getLogger("uvicorn")

Base = declarative_base()

def get_engine():
    db_url = settings.sqlalchemy_database_url
    try:
        if db_url.startswith("postgresql"):
            # Test connecting to postgresql
            engine = create_engine(db_url, pool_pre_ping=True)
            with engine.connect() as conn:
                logger.info("Successfully connected to PostgreSQL database.")
            return engine
        else:
            return create_engine(db_url, connect_args={"check_same_thread": False})
    except Exception as e:
        logger.warning(
            f"Could not connect to PostgreSQL at {db_url} ({e}). "
            "Falling back to local SQLite database 'kisan2consumer.db' for seamless execution."
        )
        sqlite_engine = create_engine(
            "sqlite:///./kisan2consumer.db",
            connect_args={"check_same_thread": False}
        )
        return sqlite_engine

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
