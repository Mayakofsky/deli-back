import secrets
import string
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from typing import List, Optional

# 1. Генератор ID (8 символов: буквы и цифры)
def generate_custom_id():
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(8))

# 2. Настройка БД
DB_URL = "postgresql://deli_user:73xlPRxx75BQ@localhost/deli_db"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 3. Модель таблицы
class UserDB(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True, default=generate_custom_id, unique=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, unique=True, nullable=False, index=True)
    link = Column(String, nullable=True)

# Создаем таблицы в Postgres
Base.metadata.create_all(bind=engine)

# 4. Схемы данных (Pydantic)
class UserCreate(BaseModel):
    first_name: str
    last_name: str
    phone: str

class UserUpdateLink(BaseModel):
    link: str

app = FastAPI()

# --- ЭНДПОИНТЫ ---

@app.post("/register")
def register(user: UserCreate):
    db = SessionLocal()
    attempts = 0
    try:
        while attempts < 5:
            new_user = UserDB(
                user_id=generate_custom_id(),
                first_name=user.first_name,
                last_name=user.last_name,
                phone=user.phone
            )
            try:
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                return new_user 
            except IntegrityError as e:
                db.rollback()
                err_msg = str(e.orig)
                if "phone" in err_msg:
                    raise HTTPException(status_code=400, detail="Этот номер телефона уже зарегистрирован")
                attempts += 1
        
        raise HTTPException(status_code=500, detail="Не удалось сгенерировать уникальный ID")
    finally:
        db.close()

@app.patch("/users/{user_id}/link")
def update_link(user_id: str, data: UserUpdateLink):
    db = SessionLocal()
    try:
        user = db.query(UserDB).filter(UserDB.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        user.link = data.link
        db.commit()
        db.refresh(user)
        return {"status": "success", "user_id": user.user_id, "new_link": user.link}
    finally:
        db.close()

@app.get("/users")
def get_all_users():
    db = SessionLocal()
    try:
        users = db.query(UserDB).all()
        return users
    finally:
        db.close()
