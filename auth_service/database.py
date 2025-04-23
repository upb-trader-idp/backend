from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

USERS_DB_URL = os.getenv("USERS_DB_URL")

if not USERS_DB_URL:
    raise ValueError("[auth_service] USERS_DB_URL environment variable is not set")

engine = create_engine(USERS_DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
