from typing import Optional
from pydantic import BaseModel

# Pydantic Schemas
class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class BalanceUpdate(BaseModel):
    amount: float

class TradeItem(BaseModel):
    symbol: str
    quantity: int
    price: float
    action: str
    flag: str = "unprocessed"

class PortfolioItem(BaseModel):
    symbol: str
    quantity: int
    price: float

class TradeUpdate(BaseModel):
    price: float | None = None
    quantity: int | None = None

class StockData(BaseModel):
    symbol: str
    current_price: float
    change_percent: float
    change_amount: float
    volume: int
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None

class HistoricalData(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int