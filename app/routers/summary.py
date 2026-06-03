from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import DebtDB, EventDB, EventParticipantDB, UserDB

router = APIRouter(prefix="/summary", tags=["summary"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/owed")
def summary_owed(user_id: str, db: Session = Depends(get_db)):
    result = []

    debts = (
        db.query(DebtDB)
        .filter(DebtDB.creditor_id == user_id, DebtDB.status == "active")
        .all()
    )
    for d in debts:
        debtor = db.query(UserDB).filter(UserDB.user_id == d.debtor_id).first()
        result.append(
            {
                "type": "debt",
                "counterparty": {
                    "user_id": debtor.user_id,
                    "first_name": debtor.first_name,
                    "last_name": debtor.last_name,
                    "photo_url": debtor.photo_url,
                }
                if debtor
                else None,
                "amount": float(d.amount),
                "description": d.description,
                "deadline": d.deadline.isoformat() if d.deadline else None,
                "debt_id": d.id,
                "photo_url": d.photo_url,
            }
        )

    events = (
        db.query(EventDB)
        .join(EventParticipantDB, EventParticipantDB.event_id == EventDB.id)
        .filter(
            EventParticipantDB.user_id == user_id,
            EventDB.status == "active",
        )
        .all()
    )
    from app.routers.events import get_balances

    for ev in events:
        balances = get_balances(ev.id, db)
        my_balance = next((b for b in balances if b["user_id"] == user_id), None)
        if my_balance and my_balance["balance"] > 0:
            debtors_in_event = [b for b in balances if b["balance"] < 0]
            result.append(
                {
                    "type": "event",
                    "event_id": ev.id,
                    "event_title": ev.title,
                    "amount": round(my_balance["balance"], 2),
                    "debtors": debtors_in_event,
                    "deadline": ev.deadline.isoformat() if ev.deadline else None,
                }
            )

    return result


@router.get("/due")
def summary_due(user_id: str, db: Session = Depends(get_db)):
    result = []

    debts = (
        db.query(DebtDB)
        .filter(DebtDB.debtor_id == user_id, DebtDB.status == "active")
        .all()
    )
    for d in debts:
        creditor = db.query(UserDB).filter(UserDB.user_id == d.creditor_id).first()
        result.append(
            {
                "type": "debt",
                "counterparty": {
                    "user_id": creditor.user_id,
                    "first_name": creditor.first_name,
                    "last_name": creditor.last_name,
                    "photo_url": creditor.photo_url,
                }
                if creditor
                else None,
                "amount": float(d.amount),
                "description": d.description,
                "deadline": d.deadline.isoformat() if d.deadline else None,
                "debt_id": d.id,
                "photo_url": d.photo_url,
            }
        )

    events = (
        db.query(EventDB)
        .join(EventParticipantDB, EventParticipantDB.event_id == EventDB.id)
        .filter(
            EventParticipantDB.user_id == user_id,
            EventDB.status == "active",
        )
        .all()
    )
    from app.routers.events import get_balances

    for ev in events:
        balances = get_balances(ev.id, db)
        my_balance = next((b for b in balances if b["user_id"] == user_id), None)
        if my_balance and my_balance["balance"] < 0:
            creditors_in_event = [b for b in balances if b["balance"] > 0]
            result.append(
                {
                    "type": "event",
                    "event_id": ev.id,
                    "event_title": ev.title,
                    "amount": round(abs(my_balance["balance"]), 2),
                    "creditors": creditors_in_event,
                    "deadline": ev.deadline.isoformat() if ev.deadline else None,
                }
            )

    return result
