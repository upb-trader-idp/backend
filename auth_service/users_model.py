from sqlalchemy import Column, Integer, String, Numeric
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    balance = Column(Numeric(12, 2), default=0.0)
    added_balance = Column(Numeric(12, 2), default=0.0)
    blocked_balance = Column(Numeric(12, 2), default=0.0)
