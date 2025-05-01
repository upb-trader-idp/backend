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
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from time import time


app = FastAPI()

# Prometheus metrics
REQUEST_COUNT = Counter(
    'auth_service_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'auth_service_request_latency_seconds',
    'Request latency in seconds',
    ['method', 'endpoint']
)

# JWT config
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 60


# Dependency to get DB session
def get_main_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# JWT Helper
def create_access_token(username: str):
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": username,
        "iss": "auth-service",
        "exp": expire
    }

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Middleware to track metrics
@app.middleware("http")
async def track_metrics(request, call_next):
    start_time = time()
    method = request.method
    endpoint = request.url.path

    try:
        response = await call_next(request)
        status_code = response.status_code
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_code).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time() - start_time)
        return response
    except Exception as e:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=500).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time() - start_time)
        raise e


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


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

    access_token = create_access_token(user.username)

    return {"access_token": access_token, "token_type": "bearer"}
