from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

# Prefer DBCON, fall back to DATABASE_URL
url = os.getenv("DBCON") or os.getenv("DATABASE_URL")
if not url:
    raise RuntimeError("DB URL not set. Define DBCON or DATABASE_URL")

# SQLAlchemy prefers postgresql:// over postgres://
if url.startswith("postgres://"):
    url = "postgresql://" + url[len("postgres://"):]

engine = create_engine(url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
