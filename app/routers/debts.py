from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import DebtDB, UserDB
from app.schemas import DebtCreate, DebtUpdate

router = APIRouter(prefix="/debts", tags=["debts"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("")
def create_debt(body: DebtCreate, db: Session = Depends(get_db)):
    creditor = db.query(UserDB).filter(UserDB.user_id == body.creditor_id).first()
    if not creditor:
        raise HTTPException(404, "Creditor not found")
    debtor = db.query(UserDB).filter(UserDB.user_id == body.debtor_id).first()
    if not debtor:
        raise HTTPException(404, "Debtor not found")

    debt = DebtDB(
        creditor_id=body.creditor_id,
        debtor_id=body.debtor_id,
        amount=body.amount,
        description=body.description,
        deadline=body.deadline,
        photo_url=body.photo_url,
    )
    db.add(debt)
    db.commit()
    db.refresh(debt)
    return _debt_full(debt, db)


@router.get("")
def list_debts(user_id: str, status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(DebtDB).filter(
        (DebtDB.creditor_id == user_id) | (DebtDB.debtor_id == user_id)
    )
    if status:
        query = query.filter(DebtDB.status == status)
    debts = query.order_by(DebtDB.created_at.desc()).all()
    return [_debt_full(d, db) for d in debts]



@router.get("/{debt_id}")
def get_debt(debt_id: str, db: Session = Depends(get_db)):
    debt = db.query(DebtDB).filter(DebtDB.id == debt_id).first()
    if not debt:
        raise HTTPException(404, "Debt not found")
    return _debt_full(debt, db)


@router.patch("/{debt_id}")
def update_debt(debt_id: str, body: DebtUpdate, db: Session = Depends(get_db)):
    debt = db.query(DebtDB).filter(DebtDB.id == debt_id).first()
    if not debt:
        raise HTTPException(404, "Debt not found")
    if body.status is not None:
        debt.status = body.status
    if body.payment_photo_url is not None:
        debt.payment_photo_url = body.payment_photo_url
    db.commit()
    return {"ok": True}


@router.delete("/{debt_id}")
def delete_debt(debt_id: str, db: Session = Depends(get_db)):
    debt = db.query(DebtDB).filter(DebtDB.id == debt_id).first()
    if not debt:
        raise HTTPException(404, "Debt not found")
    db.delete(debt)
    db.commit()
    return {"ok": True}


def _debt_full(debt: DebtDB, db: Session) -> dict:
    creditor = db.query(UserDB).filter(UserDB.user_id == debt.creditor_id).first()
    debtor = db.query(UserDB).filter(UserDB.user_id == debt.debtor_id).first()
    return {
        "id": debt.id,
        "creditor": {
            "user_id": creditor.user_id,
            "first_name": creditor.first_name,
            "last_name": creditor.last_name,
            "photo_url": creditor.photo_url,
        }
        if creditor
        else None,
        "debtor": {
            "user_id": debtor.user_id,
            "first_name": debtor.first_name,
            "last_name": debtor.last_name,
            "photo_url": debtor.photo_url,
        }
        if debtor
        else None,
        "amount": float(debt.amount),
        "description": debt.description,
        "deadline": debt.deadline.isoformat() if debt.deadline else None,
        "photo_url": debt.photo_url,
        "payment_photo_url": debt.payment_photo_url,
        "status": debt.status,
        "created_at": debt.created_at.isoformat() if debt.created_at else None,
    }
