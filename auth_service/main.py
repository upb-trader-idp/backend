from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from jose import jwt
from passlib.hash import bcrypt
from datetime import datetime, timedelta, timezone
from shared.models import User
from shared.database import SessionLocal
from shared.schemas import UserCreate, Token
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
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


# Dependency to get DB session
def get_main_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# JWT Helper
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    

# Routes
@app.post("/register")
def register(user: UserCreate,
             db: Session = Depends(get_main_db)):
    
    existing_user = db.query(User).filter(User.username == user.username).first()

    if existing_user:
        raise HTTPException(status_code=400, detail=f"Username {existing_user.username} already exists")

    hashed_pw = bcrypt.hash(user.password)
    new_user = User(username=user.username, password=hashed_pw)

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except Exception as e:
        print(f"[auth/register] Commit failed: {e}")
        db.rollback()

        raise HTTPException(status_code=500, detail="Database error")

    return {"msg": f"User {user.username} created"}


@app.post("/login", response_model=Token)
def login(user: UserCreate,
          db: Session = Depends(get_main_db)):
    
    db_user = db.query(User).filter(User.username == user.username).first()

    if not db_user or not bcrypt.verify(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.username})

    return {"access_token": access_token, "token_type": "bearer"}
