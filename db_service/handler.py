from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models import Base, Trade as TradeModel
from database import SessionLocal, engine

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables on startup
Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic schema
class Trade(BaseModel):
    username: str
    symbol: str
    quantity: int
    price: float
    action: str  # "buy" or "sell"

# Route
@app.post("/trade")
def save_trade(trade: Trade, db: Session = Depends(get_db)):
    new_trade = TradeModel(trade.model_dump())
    db.add(new_trade)
    db.commit()
    db.refresh(new_trade)
    return {"msg": "Trade saved", "trade_id": new_trade.id}
