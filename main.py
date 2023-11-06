from secrets import token_urlsafe

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from psycopg2 import connect, DatabaseError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.model import Base, User


app = FastAPI()
auth = HTTPBasic()

engine = create_engine("postgresql://postgres:postgres@localhost:5432/postgres")
Session = sessionmaker(bind=engine)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(engine)


# Define a helper function to verify the user credentials
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


# Define a helper function to create a database for a user
def create_database(user: User):
    # Generate a random database name and password
    dbname = f"db_{user.username}_{token_urlsafe(8)}"
    dbpass = token_urlsafe(16)

    conn = connect("dbname=postgres user=postgres password=postgres")
    conn.autocommit = True
    cur = conn.cursor()

    try:
        cur.execute(f"CREATE DATABASE {dbname}")
        cur.execute(f"CREATE USER {dbname} WITH PASSWORD '{dbpass}'")
        cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {dbname} TO {dbname}")
    except DatabaseError as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database creation failed: {e}",
        )
    finally:
        cur.close()
        conn.close()
    return dbname, dbname, dbpass


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/create_database")
def create_database_page(request: Request):
    return templates.TemplateResponse("create_db.html", {"request": request})


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


# Define the endpoint to authorize under a created user
@app.get("/authorize")
def authorize(user: User = Depends(verify_user)):
    return {"message": "User authorized successfully", "user_id": user.id, "username": user.username}


# Define the endpoint to create a database for a user
@app.post("/create_database")
def create_database_for_user(user: User = Depends(verify_user)):
    dbname, dbuser, dbpass = create_database(user)
    return {"message": "Database created successfully", "database": dbname, "user": dbuser, "password": dbpass}
