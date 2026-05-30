from fastapi import APIRouter, HTTPException
from sqlalchemy import func

from app.database import SessionLocal
from app.models import UserDB
from app.schemas import GuestCreate, UserUpdate

router = APIRouter()


@router.get("/users/search")
def search_users(query: str, current_user_id: str):
    db = SessionLocal()
    try:
        if not query.strip():
            return []

        search_pattern = f"%{query.strip()}%"

        full_name_concat = func.concat(UserDB.first_name, " ", UserDB.last_name)
        reverse_name_concat = func.concat(UserDB.last_name, " ", UserDB.first_name)

        users = (
            db.query(UserDB)
            .filter(
                (UserDB.first_name.ilike(search_pattern))
                | (UserDB.last_name.ilike(search_pattern))
                | (UserDB.email.ilike(search_pattern))
                | (full_name_concat.ilike(search_pattern))
                | (reverse_name_concat.ilike(search_pattern))
            )
            .filter(UserDB.user_id != current_user_id)
            .all()
        )

        result = []
        for u in users:
            result.append(
                {
                    "user_id": u.user_id,
                    "email": u.email,
                    "first_name": u.first_name,
                    "last_name": u.last_name,
                    "link": u.link,
                    "photo_url": u.photo_url,
                }
            )
        return result
    finally:
        db.close()


@router.get("/users/{user_id}")
def get_user(user_id: str):
    db = SessionLocal()
    try:
        user = db.query(UserDB).filter(UserDB.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "user_id": user.user_id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "link": user.link,
            "photo_url": user.photo_url,
        }
    finally:
        db.close()


@router.patch("/users/{user_id}")
def update_user(user_id: str, body: UserUpdate):
    db = SessionLocal()
    try:
        user = db.query(UserDB).filter(UserDB.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.link = body.link
        if body.photo_url is not None:
            user.photo_url = body.photo_url
        db.commit()
        return {"ok": True}
    finally:
        db.close()


@router.post("/users/guest")
def create_guest(body: GuestCreate):
    db = SessionLocal()
    try:
        guest = UserDB(first_name=body.name, last_name="", is_guest=True)
        db.add(guest)
        db.commit()
        db.refresh(guest)
        return {
            "user_id": guest.user_id,
            "first_name": guest.first_name,
            "last_name": guest.last_name,
        }
    finally:
        db.close()
