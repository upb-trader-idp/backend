from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

MAIN_DB_URL = os.getenv("MAIN_DB_URL")

if not MAIN_DB_URL:
    raise ValueError("MAIN_DB_URL environment variable is not set")

engine = create_engine(MAIN_DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
