import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Only load .env locally
if not os.getenv("RENDER"):
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass

url = os.getenv("DBCON") or os.getenv("DATABASE_URL")
if not url:
    raise RuntimeError("DB URL not set. Define DBCON or DATABASE_URL")

# Normalize scheme and force SSL on Render
if url.startswith("postgres://"):
    url = "postgresql://" + url[len("postgres://"):]
if os.getenv("RENDER") and "sslmode=" not in url:
    url += ("&" if "?" in url else "?") + "sslmode=require"

# TEMP: log host only (no secrets) to confirm we're not on localhost
try:
    host = url.split("@", 1)[-1].split("/", 1)[0]
    print("DB HOST:", host)
except Exception:
    pass

engine = create_engine(url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()