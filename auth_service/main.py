from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from fastapi import Security
from jose import jwt, JWTError
from passlib.hash import bcrypt
from datetime import datetime, timedelta, timezone
from models import Base, User
from database import SessionLocal, engine
from pydantic import BaseModel
import os
from decimal import Decimal


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # FIXME: Set to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Create tables
Base.metadata.create_all(bind=engine)


# JWT config
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic Schemas
class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class BalanceUpdate(BaseModel):
    amount: float


# JWT Helper
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Get current username from JWT token
def get_current_username(credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    

# Routes
@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()

    if existing_user:
        raise HTTPException(status_code=400, detail=f"Username {existing_user.username} already exists")

    hashed_pw = bcrypt.hash(user.password)
    new_user = User(username=user.username, password=hashed_pw)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"msg": f"User {user.username} created"}


@app.post("/login", response_model=Token)
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()

    if not db_user or not bcrypt.verify(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.username})

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/get_balance")
def get_balance(username: str = Depends(get_current_username), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"username": username, "balance": float(user.balance)}


@app.post("/add_balance")
def add_balance(update: BalanceUpdate, username: str = Depends(get_current_username), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if update.amount < 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    user.balance += Decimal(str(update.amount))
    user.added_balance += Decimal(str(update.amount))

    db.commit()
    db.refresh(user)

    return {"msg": f"Balance updated for {username}", "new_balance": float(user.balance)}


@app.post("/remove_balance")
def remove_balance(update: BalanceUpdate, username: str = Depends(get_current_username), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if update.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    amount = Decimal(str(update.amount))

    if user.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    user.balance -= amount

    db.commit()
    db.refresh(user)

    return {"msg": f"Balance removed for {username}", "new_balance": float(user.balance)}