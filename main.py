import secrets
import string

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import Boolean, Column, String, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# --- ГЕНЕРАТОРЫ ---
def generate_custom_id():
    return "".join(
        secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8)
    )


def generate_verify_code():
    return "".join(secrets.choice(string.digits) for _ in range(6))


# --- НАСТРОЙКА БД ---
DB_URL = "postgresql://deli_user:73xlPRxx75BQ@localhost/deli_db"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- МОДЕЛЬ ТАБЛИЦЫ ---
class UserDB(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True, default=generate_custom_id, unique=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String, nullable=True)
    link = Column(String, nullable=True)


Base.metadata.create_all(bind=engine)


# --- СХЕМЫ ДАННЫХ ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str


class VerifyRequest(BaseModel):
    email: str
    code: str


app = FastAPI()

# --- ЭНДПОИНТЫ ---


@app.post("/register")
def register(user: UserCreate):
    db = SessionLocal()
    try:
        code = generate_verify_code()
        new_user = UserDB(
            email=user.email,
            password=user.password,
            first_name=user.first_name,
            last_name=user.last_name,
            verification_code=code,
        )
        db.add(new_user)
        db.commit()

        # Печатаем код в консоль сервера
        print(f"\n[!] КОД ВЕРИФИКАЦИИ ДЛЯ {user.email}: {code}\n")

        return {"status": "success", "message": "Check server console for code"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already exists")
    finally:
        db.close()


@app.post("/verify")
def verify(data: VerifyRequest):
    db = SessionLocal()
    try:
        user = db.query(UserDB).filter(UserDB.email == data.email).first()
        if not user or user.verification_code != data.code:
            raise HTTPException(status_code=400, detail="Invalid code or email")

        user.is_verified = True
        user.verification_code = None
        db.commit()
        return {"status": "verified", "user_id": user.user_id}
    finally:
        db.close()
