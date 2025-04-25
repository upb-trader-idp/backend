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