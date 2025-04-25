from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from pydantic import BaseModel
from decimal import Decimal
import os

from database import SessionLocal
from users_model import User, Portfolio
from trades_model import Trade as TradeModel
from typing import List

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # FIXME: Set to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# DB deps
def get_main_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

# JWT helper
security = HTTPBearer()

def get_current_username(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Pydantic schemas
class BalanceUpdate(BaseModel):
    amount: float

class Trade(BaseModel):
    symbol: str
    quantity: int
    price: float
    action: str
    flag: str = "unprocessed"

class PortfolioItem(BaseModel):
    symbol: str
    quantity: int
    price: float


# Balance endpoints
@app.get("/get_balance")
def get_balance(username: str = Depends(get_current_username),
                db: Session = Depends(get_main_db)):
    
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"username": username, "balance": float(user.balance)}


@app.post("/add_balance")
def add_balance(update: BalanceUpdate,
                username: str = Depends(get_current_username),
                db: Session = Depends(get_main_db)):
    
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if update.amount < 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    user.balance += Decimal(str(update.amount))
    user.added_balance += Decimal(str(update.amount))

    db.commit()
    db.refresh(user)

    return {"msg": f"Balance updated", "new_balance": float(user.balance)}


@app.post("/remove_balance")
def remove_balance(update: BalanceUpdate,
                   username: str = Depends(get_current_username),
                   db: Session = Depends(get_main_db)):
    
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    amount = Decimal(str(update.amount))

    if user.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    user.balance -= amount

    db.commit()
    db.refresh(user)

    return {"msg": f"Balance removed", "new_balance": float(user.balance)}


# Trade endpoint
@app.post("/add_trade")
def add_trade(trade: Trade,
              main_db: Session = Depends(get_main_db),
              username: str = Depends(get_current_username)):
    
    
    user = main_db.query(User).filter(User.username == username).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    total_cost = Decimal(str(trade.quantity * trade.price))

    if trade.action == "buy":
        if user.balance < total_cost:
            raise HTTPException(status_code=400, detail="Insufficient balance for buy order")

        user.balance -= total_cost 

        main_db.commit()
        main_db.refresh(user)


    elif trade.action == "sell":
        holding = main_db.query(Portfolio).filter(
            Portfolio.username == username,
            Portfolio.symbol == trade.symbol
        ).first()

        if not holding or holding.quantity < trade.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient shares of {trade.symbol} to sell")

        # Remove shares from portfolio
        holding.quantity -= trade.quantity

        if holding.quantity == 0:
            main_db.delete(holding)

        main_db.commit()
        main_db.refresh(user)

    else:
        raise HTTPException(status_code=400, detail="Invalid trade action")
    

    new_trade = TradeModel(username=username, **trade.model_dump(exclude={"created_at"}))
    main_db.add(new_trade)
    main_db.commit()
    main_db.refresh(new_trade)

    return {"msg": "Trade added", "trade_id": new_trade.id}


@app.get("/get_portfolio", response_model=List[PortfolioItem])
def get_portfolio(username: str = Depends(get_current_username),
                  db: Session = Depends(get_main_db)):
    
    return db.query(Portfolio).filter(Portfolio.username == username).all()


