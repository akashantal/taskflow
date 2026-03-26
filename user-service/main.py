from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, String, DateTime, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
import os, uuid

app = FastAPI(title="User Service")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://taskuser:taskpass@localhost:5432/taskflow")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    id         = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username   = Column(String, unique=True, nullable=False)
    email      = Column(String, unique=True, nullable=False)
    password   = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "user-service running"}

@app.post("/register", status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(
        username=req.username,
        email=req.email,
        password=pwd_context.hash(req.password)
    )
    db.add(user)
    db.commit()
    return {"message": "User registered successfully", "user_id": user.id}

@app.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not pwd_context.verify(req.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = jwt.encode(
        {"sub": user.id, "exp": datetime.utcnow() + timedelta(hours=24)},
        SECRET_KEY, algorithm="HS256"
    )
    return {"access_token": token, "token_type": "bearer"}

@app.get("/users/{user_id}")
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "username": user.username, "email": user.email}
