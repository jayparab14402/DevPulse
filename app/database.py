import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# .env file se environment variables load karega
load_dotenv()

# PostgreSQL connection URL
DATABASE_URL = os.getenv("ENGINE")

if not DATABASE_URL:
    raise ValueError("ENGINE is missing from .env file")

# Engine application mein ek baar create hoga
# pool_pre_ping=True stale DB connections check karta hai
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# Session factory - jab call karoge naya Session milega
SessionLocal = sessionmaker(bind=engine)


def create_sql_session():
    # Naya database Session return karega
    return SessionLocal()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()