from fastapi import APIRouter
from sqlalchemy import func

from app.database import SessionLocal
from app.models import UserDB

router = APIRouter()


@router.get("/users/search")
def search_users(query: str, current_user_id: str):
    db = SessionLocal()
    try:
        print(f"\n[SEARCH] Начало поиска для query='{query}'")

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

        print(f"[SEARCH] База вернула строк: {len(users)}")
        for u in users:
            print(
                f"  -> Найдено в БД: ID={u.user_id} | Name={u.first_name} | Surname={u.last_name} | Email={u.email} | Link={u.link}"
            )

        result = []
        for u in users:
            result.append(
                {
                    "user_id": u.user_id,
                    "email": u.email,
                    "first_name": u.first_name,
                    "last_name": u.last_name,
                }
            )
        return result
    finally:
        db.close()
