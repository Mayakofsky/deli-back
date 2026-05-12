from fastapi import APIRouter, HTTPException
from sqlalchemy import or_

from app.database import SessionLocal
from app.models import FriendshipDB, UserDB
from app.schemas import FriendRequest, FriendRespond

router = APIRouter()


@router.post("/friends/send")
def send_request(req: FriendRequest):
    db = SessionLocal()
    try:
        existing = (
            db.query(FriendshipDB)
            .filter(
                or_(
                    (FriendshipDB.user_id == req.user_id)
                    & (FriendshipDB.friend_id == req.friend_id),
                    (FriendshipDB.user_id == req.friend_id)
                    & (FriendshipDB.friend_id == req.user_id),
                )
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Friendship already exists")

        friendship = FriendshipDB(
            user_id=req.user_id, friend_id=req.friend_id, status="pending"
        )
        db.add(friendship)
        db.commit()
        return {"status": "success", "message": "Friend request sent"}
    finally:
        db.close()


@router.post("/friends/respond")
def respond_request(req: FriendRespond):
    if req.action not in ("accept", "reject"):
        raise HTTPException(status_code=400, detail="Action must be 'accept' or 'reject'")

    db = SessionLocal()
    try:
        friendship = (
            db.query(FriendshipDB)
            .filter(
                FriendshipDB.user_id == req.friend_id,
                FriendshipDB.friend_id == req.user_id,
                FriendshipDB.status == "pending",
            )
            .first()
        )
        if not friendship:
            raise HTTPException(status_code=404, detail="Friend request not found")

        if req.action == "accept":
            friendship.status = "accepted"
        else:
            friendship.status = "rejected"

        db.commit()
        return {"status": "success", "message": f"Request {req.action}ed"}
    finally:
        db.close()


@router.post("/friends/unsend")
def unsend_request(req: FriendRequest):
    db = SessionLocal()
    try:
        friendship = (
            db.query(FriendshipDB)
            .filter(
                FriendshipDB.user_id == req.user_id,
                FriendshipDB.friend_id == req.friend_id,
                FriendshipDB.status == "pending",
            )
            .first()
        )
        if not friendship:
            raise HTTPException(status_code=404, detail="Friend request not found")

        db.delete(friendship)
        db.commit()
        return {"status": "success", "message": "Friend request cancelled"}
    finally:
        db.close()


def _user_dict(u: UserDB) -> dict:
    return {
        "user_id": u.user_id,
        "email": u.email,
        "first_name": u.first_name,
        "last_name": u.last_name,
    }


@router.get("/friends/incoming")
def incoming_requests(user_id: str):
    db = SessionLocal()
    try:
        rows = (
            db.query(FriendshipDB, UserDB)
            .join(UserDB, FriendshipDB.user_id == UserDB.user_id)
            .filter(
                FriendshipDB.friend_id == user_id,
                FriendshipDB.status == "pending",
            )
            .all()
        )
        return [_user_dict(user) for _, user in rows]
    finally:
        db.close()


@router.get("/friends/outgoing")
def outgoing_requests(user_id: str):
    db = SessionLocal()
    try:
        rows = (
            db.query(FriendshipDB, UserDB)
            .join(UserDB, FriendshipDB.friend_id == UserDB.user_id)
            .filter(
                FriendshipDB.user_id == user_id,
                FriendshipDB.status == "pending",
            )
            .all()
        )
        return [_user_dict(user) for _, user in rows]
    finally:
        db.close()


@router.get("/friends/list")
def friends_list(user_id: str):
    db = SessionLocal()
    try:
        as_user = (
            db.query(FriendshipDB, UserDB)
            .join(UserDB, FriendshipDB.friend_id == UserDB.user_id)
            .filter(
                FriendshipDB.user_id == user_id,
                FriendshipDB.status == "accepted",
            )
            .all()
        )
        as_friend = (
            db.query(FriendshipDB, UserDB)
            .join(UserDB, FriendshipDB.user_id == UserDB.user_id)
            .filter(
                FriendshipDB.friend_id == user_id,
                FriendshipDB.status == "accepted",
            )
            .all()
        )
        result = [_user_dict(user) for _, user in as_user]
        result.extend(_user_dict(user) for _, user in as_friend)
        return result
    finally:
        db.close()

