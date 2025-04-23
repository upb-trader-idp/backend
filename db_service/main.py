from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Security
from jose import jwt, JWTError
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models import Base, Trade as TradeModel
from database import SessionLocal, engine
import os


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # FIXME: Set to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# JWT config
SECRET_KEY = os.getenv("JWT_SECRET")  # shared with auth_service
ALGORITHM = "HS256"


# Create table
Base.metadata.create_all(bind=engine)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Get current username from JWT token
def get_current_username(credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


class Trade(BaseModel):
    symbol: str
    quantity: int
    price: float
    action: str
    flag: str = "unprocessed"

#Routes
@app.post("/trade")
def save_trade(trade: Trade, db: Session = Depends(get_db), username: str = Depends(get_current_username)):
    new_trade = TradeModel(username=username, **trade.model_dump())

    db.add(new_trade)
    db.commit()
    db.refresh(new_trade)
    
    return {"msg": "Trade saved", "trade_id": new_trade.id}
