from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import UserDB
from app.schemas import UserCreate, UserLogin

router = APIRouter()


@router.post("/register")
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
        return {
            "status": "success",
            "user_id": new_user.user_id,
            "message": "User registered",
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already exists")
    finally:
        db.close()


@router.post("/login")
def login(credentials: UserLogin):
    db = SessionLocal()
    try:
        user = db.query(UserDB).filter(UserDB.email == credentials.email).first()
        if not user or user.password != credentials.password:
            raise HTTPException(status_code=400, detail="Invalid email or password")
        return {"status": "success", "user_id": user.user_id, "message": "Logged in"}
    finally:
        db.close()
