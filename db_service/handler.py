from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2
import os

app = FastAPI()

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
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO trades (username, symbol, quantity, price, action)
        VALUES (%s, %s, %s, %s, %s)
    """, (trade.username, trade.symbol, trade.quantity, trade.price, trade.action))
    conn.commit()
    cur.close()
    conn.close()
    return {"msg": "Trade saved"}
