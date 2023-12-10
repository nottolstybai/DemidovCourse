import os
from datetime import datetime, timedelta
from secrets import token_urlsafe
from typing import Type

import jwt
import psycopg2
from fastapi import FastAPI, Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.model import Base, User

app = FastAPI()
auth = HTTPBasic()

host = os.getenv("DB_HOST")
engine = create_engine(f"postgresql://postgres:postgres@{host}:5432/postgres")
Session = sessionmaker(bind=engine)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(engine)


def create_jwt_token(user_id: int):
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=1)
    }
    token = jwt.encode(payload, "secret", algorithm="HS256")
    return token


def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
        user_id = payload["sub"]
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_user(credentials: HTTPBasicCredentials = Depends(auth)):
    session = Session()
    user = session.query(User).filter_by(username=credentials.username).first()
    if not user or user.password != credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user


def create_database(user: Type[User]):
    dbname = f"db_{user.username}_{token_urlsafe(8)}"
    dbpass = token_urlsafe(16)

    conn = psycopg2.connect(host=host,
                            database="postgres",
                            user="postgres",
                            password="postgres")
    conn.autocommit = True
    cur = conn.cursor()

    try:
        cur.execute(f"CREATE DATABASE {dbname}")
        cur.execute(f"CREATE USER {dbname} WITH PASSWORD '{dbpass}'")
        cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {dbname} TO {dbname}")
    except psycopg2.DatabaseError as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database creation failed: {e}",
        )
    finally:
        cur.close()
        conn.close()
    return dbname, dbname, dbpass


@app.post("/register")
def register(credentials: HTTPBasicCredentials = Depends(auth)):
    session = Session()
    if session.query(User).filter_by(username=credentials.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    user = User(username=credentials.username, password=credentials.password)
    session.add(user)
    session.commit()
    return {"message": "User registered successfully"}


@app.post("/authorize")
def authorize(user: User = Depends(verify_user)):
    token = create_jwt_token(user.id)
    return {"message": "User authorized successfully", "user_id": user.id, "username": user.username, "token": token}


@app.get("/create_database")
def create_database_for_user(token: str = Header(None)):
    user_id = verify_jwt_token(token)
    session = Session()
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    dbname, dbuser, dbpass = create_database(user)
    return {"message": "Database created successfully", "database": dbname, "user": dbuser, "password": dbpass}


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
