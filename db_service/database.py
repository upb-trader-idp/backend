from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

USERS_DB_URL = os.getenv("USERS_DB_URL")
TRADING_DB_URL = os.getenv("TRADING_DB_URL")

if not USERS_DB_URL:
    raise ValueError("[db_service] USERS_DB_URL environment variable is not set")

if not TRADING_DB_URL:
    raise ValueError("[db_service] TRADING_DB_URL environment variable is not set")

users_engine = create_engine(USERS_DB_URL)
trading_engine = create_engine(TRADING_DB_URL)

UsersSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=users_engine)
TradingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=trading_engine)
