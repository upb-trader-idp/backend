from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from passlib.hash import bcrypt
from jose import JWTError, jwt
import psycopg2
import os
from datetime import datetime, timedelta

app = FastAPI()

# JWT
SECRET_KEY = os.getenv("JWT_SECRET", "supersecret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# DB connectionection
def get_db():
    return psycopg2.connectionect(
        dbname="users_db",
        user="postgres",
        password="postgres",
        host="users_db",
        port="5432"
    )


# Models
class UserCreate(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


# JWT Helpers
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Routes
@app.post("/register")
def register(user: UserCreate):
    connection = get_db()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM users WHERE username = %s", (user.username,))

    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_pw = bcrypt.hash(user.password)

    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (user.username, hashed_pw))
    connection.commit()
    cursor.close()
    connection.close()

    return {"msg": "User created"}


@app.post("/login", response_model=Token)
def login(user: UserCreate):
    connection = get_db()
    cursor = connection.cursor()

    cursor.execute("SELECT password FROM users WHERE username = %s", (user.username,))
    result = cursor.fetchone()

    if not result or not bcrypt.verify(user.password, result[0]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.username})
    
    return {"access_token": access_token, "token_type": "bearer"}
