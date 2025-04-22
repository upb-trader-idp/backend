from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # FIXME: Set to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB connection
def get_db():
    return psycopg2.connect(
        dbname="trading_db",
        user="postgres",
        password="postgres",
        host="trading_db",
        port="5432"
    )

# Models
class Trade(BaseModel):
    username: str
    symbol: str
    quantity: int
    price: float
    action: str  # "buy" or "sell"

# Routes
@app.post("/trade")
def save_trade(trade: Trade):
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO trades (username, symbol, quantity, price, action)
        VALUES (%s, %s, %s, %s, %s)
    """, (trade.username, trade.symbol, trade.quantity, trade.price, trade.action))
    connection.commit()
    cursor.close()
    connection.close()
    return {"msg": "Trade saved"}
