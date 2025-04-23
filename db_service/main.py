from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from pydantic import BaseModel
from decimal import Decimal
import os

from database import UsersSessionLocal, TradingSessionLocal
from users_model import User
from trades_model import Trade as TradeModel

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
def get_users_db():
    db = UsersSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_trading_db():
    db = TradingSessionLocal()
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


# Balance endpoints
@app.get("/get_balance")
def get_balance(username: str = Depends(get_current_username), db: Session = Depends(get_users_db)):
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"username": username, "balance": float(user.balance)}

@app.post("/add_balance")
def add_balance(update: BalanceUpdate, username: str = Depends(get_current_username), db: Session = Depends(get_users_db)):
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
def remove_balance(update: BalanceUpdate, username: str = Depends(get_current_username), db: Session = Depends(get_users_db)):
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


@app.post("/block_balance")
def block_balance(update: BalanceUpdate, username: str = Depends(get_current_username), db: Session = Depends(get_users_db)):
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    amount = Decimal(str(update.amount))

    if user.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    user.balance -= amount
    user.blocked_balance += amount

    db.commit()
    db.refresh(user)

    return {"msg": f"Balance blocked", "new_balance": float(user.balance)}


# Trade endpoint
@app.post("/add_trade")
def add_trade(trade: Trade, db: Session = Depends(get_trading_db), username: str = Depends(get_current_username)):
    new_trade = TradeModel(username=username, **trade.model_dump())

    db.add(new_trade)
    db.commit()
    db.refresh(new_trade)
    
    return {"msg": "Trade added", "trade_id": new_trade.id}
