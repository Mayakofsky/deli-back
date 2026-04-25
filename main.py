import secrets
import string

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, String, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# --- ГЕНЕРАТОР УНИКАЛЬНЫХ ID ---
def generate_custom_id():
    return "USR-" + "".join(
        secrets.choice(string.ascii_uppercase + string.digits) for _ in range(5)
    )


# --- НАСТРОЙКА БАЗЫ ДАННЫХ ---
DB_URL = "postgresql://deli_user:73xlPRxx75BQ@localhost/deli_db"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- МОДЕЛЬ ТАБЛИЦЫ В БД (users) ---
class UserDB(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, default=generate_custom_id, unique=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    link = Column(String, nullable=True)  # Твоё необязательное поле для ссылки!


# Автоматически создаем таблицы в базе данных при старте
Base.metadata.create_all(bind=engine)


# --- СХЕМЫ ДАННЫХ (Pydantic для валидации JSON) ---
class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    link: str | None = None  # Ссылка может быть null


app = FastAPI()


# --- ЭНДПОИНТ РЕГИСТРАЦИИ ---
@app.post("/register")
def register(user: UserCreate):
    db = SessionLocal()
    try:
        new_user = UserDB(
            email=user.email,
            password=user.password,
            first_name=user.first_name,
            last_name=user.last_name,
            link=user.link,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        print(f"[+] Успешная регистрация пользователя: {user.email}")
        return {
            "status": "success",
            "user_id": new_user.user_id,
            "message": "User successfully registered",
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already exists")
    finally:
        db.close()


# --- ЭНДПОИНТ ВХОДА (ТЕПЕРЬ СТОИТ ОТДЕЛЬНО И БЕЗ ОТСТУПОВ) ---
@app.post("/login")
def login(credentials: UserLogin):
    db = SessionLocal()
    try:
        # Ищем пользователя по почте
        user = db.query(UserDB).filter(UserDB.email == credentials.email).first()

        # Если юзер не найден или пароль не совпал
        if not user or user.password != credentials.password:
            raise HTTPException(status_code=400, detail="Invalid email or password")

        print(f"[+] Успешный вход: {user.email}")
        return {
            "status": "success",
            "user_id": user.user_id,
            "message": "Successfully logged in",
        }
    finally:
        db.close()
