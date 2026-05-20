from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    EventDB,
    EventParticipantDB,
    EventPurchaseDB,
    PurchaseBeneficiaryDB,
    UserDB,
)
from app.schemas import EventCreate, EventUpdate, GuestCreate, ParticipantAdd, PurchaseCreate, PurchaseUpdate

router = APIRouter(prefix="/events", tags=["events"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("")
def create_event(body: EventCreate, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.user_id == body.creator_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    event = EventDB(creator_id=body.creator_id, title=body.title, deadline=body.deadline)
    db.add(event)
    db.flush()

    participant = EventParticipantDB(event_id=event.id, user_id=body.creator_id)
    db.add(participant)

    for pid in body.participant_ids:
        u = db.query(UserDB).filter(UserDB.user_id == pid).first()
        if u:
            existing = (
                db.query(EventParticipantDB)
                .filter(
                    EventParticipantDB.event_id == event.id,
                    EventParticipantDB.user_id == pid,
                )
                .first()
            )
            if not existing:
                db.add(EventParticipantDB(event_id=event.id, user_id=pid))

    for gname in body.guest_names:
        guest = UserDB(first_name=gname, last_name="", is_guest=True)
        db.add(guest)
        db.flush()
        db.add(EventParticipantDB(event_id=event.id, user_id=guest.user_id))

    db.commit()
    db.refresh(event)
    return _event_full(event, db)


@router.get("")
def list_events(user_id: str, db: Session = Depends(get_db)):
    events = (
        db.query(EventDB)
        .join(EventParticipantDB, EventParticipantDB.event_id == EventDB.id)
        .filter(EventParticipantDB.user_id == user_id)
        .order_by(EventDB.created_at.desc())
        .all()
    )
    return [_event_full(event, db) for event in events]


@router.get("/{event_id}")
def get_event(event_id: str, db: Session = Depends(get_db)):
    event = db.query(EventDB).filter(EventDB.id == event_id).first()
    if not event:
        raise HTTPException(404, "Event not found")
    return _event_full(event, db)


@router.patch("/{event_id}")
def update_event(event_id: str, body: EventUpdate, db: Session = Depends(get_db)):
    event = db.query(EventDB).filter(EventDB.id == event_id).first()
    if not event:
        raise HTTPException(404, "Event not found")
    if body.title is not None:
        event.title = body.title
    if body.deadline is not None:
        event.deadline = body.deadline
    db.commit()
    db.refresh(event)
    return _event_full(event, db)


@router.post("/{event_id}/close")
def close_event(event_id: str, db: Session = Depends(get_db)):
    event = db.query(EventDB).filter(EventDB.id == event_id).first()
    if not event:
        raise HTTPException(404, "Event not found")
    event.status = "closed"
    db.commit()
    return {"ok": True}


@router.post("/{event_id}/participants")
def add_participant(event_id: str, body: ParticipantAdd, db: Session = Depends(get_db)):
    event = db.query(EventDB).filter(EventDB.id == event_id).first()
    if not event:
        raise HTTPException(404, "Event not found")

    user = db.query(UserDB).filter(UserDB.user_id == body.user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    existing = (
        db.query(EventParticipantDB)
        .filter(
            EventParticipantDB.event_id == event_id,
            EventParticipantDB.user_id == body.user_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(400, "Already a participant")

    participant = EventParticipantDB(event_id=event_id, user_id=body.user_id)
    db.add(participant)
    db.commit()
    return {"ok": True}


@router.delete("/{event_id}/participants/{user_id}")
def remove_participant(event_id: str, user_id: str, db: Session = Depends(get_db)):
    p = (
        db.query(EventParticipantDB)
        .filter(
            EventParticipantDB.event_id == event_id,
            EventParticipantDB.user_id == user_id,
        )
        .first()
    )
    if not p:
        raise HTTPException(404, "Participant not found")

    balances = get_balances(event_id, db)
    for b in balances:
        if b["user_id"] == user_id and abs(b["balance"]) > 0.01:
            raise HTTPException(400, "Cannot remove participant with outstanding balance")

    db.delete(p)
    db.commit()
    return {"ok": True}


@router.get("/{event_id}/participants")
def list_participants(event_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(EventParticipantDB, UserDB)
        .join(UserDB, EventParticipantDB.user_id == UserDB.user_id)
        .filter(EventParticipantDB.event_id == event_id)
        .all()
    )
    return [
        {
            "user_id": u.user_id,
            "first_name": u.first_name,
            "last_name": u.last_name,
        }
        for _, u in rows
    ]


@router.post("/{event_id}/guests")
def add_guest(event_id: str, body: GuestCreate, db: Session = Depends(get_db)):
    event = db.query(EventDB).filter(EventDB.id == event_id).first()
    if not event:
        raise HTTPException(404, "Event not found")

    guest = UserDB(first_name=body.name, last_name="", is_guest=True)
    db.add(guest)
    db.flush()

    participant = EventParticipantDB(event_id=event_id, user_id=guest.user_id)
    db.add(participant)
    db.commit()

    return {
        "user_id": guest.user_id,
        "first_name": guest.first_name,
        "last_name": guest.last_name,
    }


@router.post("/{event_id}/purchases")
def add_purchase(event_id: str, body: PurchaseCreate, db: Session = Depends(get_db)):
    event = db.query(EventDB).filter(EventDB.id == event_id).first()
    if not event:
        raise HTTPException(404, "Event not found")

    purchase = EventPurchaseDB(
        event_id=event_id,
        buyer_id=body.buyer_id,
        description=body.description,
        amount=body.amount,
        receipt_photo_url=body.receipt_photo_url,
    )
    db.add(purchase)
    db.flush()

    beneficiaries = body.beneficiary_ids if body.beneficiary_ids else []
    if not beneficiaries:
        participants = (
            db.query(EventParticipantDB)
            .filter(EventParticipantDB.event_id == event_id)
            .all()
        )
        beneficiaries = [p.user_id for p in participants if p.user_id != body.buyer_id]

    if beneficiaries:
        share = round(body.amount / len(beneficiaries), 2)
        for bid in beneficiaries:
            db.add(
                PurchaseBeneficiaryDB(
                    purchase_id=purchase.id,
                    user_id=bid,
                    share_amount=share,
                )
            )

    db.commit()
    db.refresh(purchase)
    return _purchase_full(purchase, db)


@router.patch("/{event_id}/purchases/{purchase_id}")
def update_purchase(event_id: str, purchase_id: str, body: PurchaseUpdate, db: Session = Depends(get_db)):
    purchase = (
        db.query(EventPurchaseDB)
        .filter(
            EventPurchaseDB.event_id == event_id,
            EventPurchaseDB.id == purchase_id,
        )
        .first()
    )
    if not purchase:
        raise HTTPException(404, "Purchase not found")

    if body.description is not None:
        purchase.description = body.description
    if body.amount is not None:
        purchase.amount = body.amount

    if body.beneficiary_ids is not None:
        db.query(PurchaseBeneficiaryDB).filter(
            PurchaseBeneficiaryDB.purchase_id == purchase_id
        ).delete()
        if body.beneficiary_ids:
            effective_amount = body.amount if body.amount is not None else float(purchase.amount)
            share = round(effective_amount / len(body.beneficiary_ids), 2)
            for bid in body.beneficiary_ids:
                db.add(
                    PurchaseBeneficiaryDB(
                        purchase_id=purchase.id,
                        user_id=bid,
                        share_amount=share,
                    )
                )

    db.commit()
    db.refresh(purchase)
    return _purchase_full(purchase, db)


@router.get("/{event_id}/purchases")
def list_purchases(event_id: str, db: Session = Depends(get_db)):
    purchases = (
        db.query(EventPurchaseDB)
        .filter(EventPurchaseDB.event_id == event_id)
        .order_by(EventPurchaseDB.created_at.desc())
        .all()
    )
    return [_purchase_full(p, db) for p in purchases]


@router.delete("/{event_id}/purchases/{purchase_id}")
def delete_purchase(event_id: str, purchase_id: str, db: Session = Depends(get_db)):
    p = (
        db.query(EventPurchaseDB)
        .filter(
            EventPurchaseDB.event_id == event_id,
            EventPurchaseDB.id == purchase_id,
        )
        .first()
    )
    if not p:
        raise HTTPException(404, "Purchase not found")
    db.delete(p)
    db.commit()
    return {"ok": True}


@router.get("/{event_id}/balances")
def get_balances(event_id: str, db: Session = Depends(get_db)):
    purchases = (
        db.query(EventPurchaseDB)
        .filter(EventPurchaseDB.event_id == event_id)
        .all()
    )

    balance_map: dict[str, float] = {}
    for p in purchases:
        buyer_id = p.buyer_id
        if buyer_id:
            balance_map[buyer_id] = balance_map.get(buyer_id, 0) + float(p.amount)

        beneficiaries = (
            db.query(PurchaseBeneficiaryDB)
            .filter(PurchaseBeneficiaryDB.purchase_id == p.id)
            .all()
        )
        for b in beneficiaries:
            balance_map[b.user_id] = (
                balance_map.get(b.user_id, 0) - float(b.share_amount)
            )

    participants = (
        db.query(EventParticipantDB, UserDB)
        .join(UserDB, EventParticipantDB.user_id == UserDB.user_id)
        .filter(EventParticipantDB.event_id == event_id)
        .all()
    )
    return [
        {
            "user_id": u.user_id,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "balance": round(balance_map.get(u.user_id, 0), 2),
        }
        for _, u in participants
    ]


@router.get("/{event_id}/settlement")
def get_settlement(event_id: str, db: Session = Depends(get_db)):
    balances_data = get_balances(event_id, db)
    balances = {b["user_id"]: b["balance"] for b in balances_data}
    user_map = {b["user_id"]: b for b in balances_data}

    debtors = [(uid, -amt) for uid, amt in balances.items() if amt < 0]
    creditors = [(uid, amt) for uid, amt in balances.items() if amt > 0]

    debtors.sort(key=lambda x: -x[1])
    creditors.sort(key=lambda x: -x[1])

    transactions = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        d_uid, d_amt = debtors[i]
        c_uid, c_amt = creditors[j]
        amount = min(d_amt, c_amt)
        if amount > 0.01:
            transactions.append(
                {
                    "from": user_map[d_uid],
                    "to": user_map[c_uid],
                    "amount": round(amount, 2),
                }
            )
        debtors[i] = (d_uid, d_amt - amount)
        creditors[j] = (c_uid, c_amt - amount)
        if debtors[i][1] < 0.01:
            i += 1
        if creditors[j][1] < 0.01:
            j += 1

    return transactions


def _event_full(event: EventDB, db: Session) -> dict:
    participants = (
        db.query(EventParticipantDB, UserDB)
        .join(UserDB, EventParticipantDB.user_id == UserDB.user_id)
        .filter(EventParticipantDB.event_id == event.id)
        .all()
    )
    balances = get_balances(event.id, db)
    return {
        "id": event.id,
        "creator_id": event.creator_id,
        "title": event.title,
        "deadline": event.deadline.isoformat() if event.deadline else None,
        "status": event.status,
        "created_at": event.created_at.isoformat() if event.created_at else None,
        "participants": [
            {
                "user_id": u.user_id,
                "first_name": u.first_name,
                "last_name": u.last_name,
            }
            for _, u in participants
        ],
        "balances": balances,
    }


def _purchase_full(purchase: EventPurchaseDB, db: Session) -> dict:
    beneficiaries = (
        db.query(PurchaseBeneficiaryDB, UserDB)
        .join(UserDB, PurchaseBeneficiaryDB.user_id == UserDB.user_id)
        .filter(PurchaseBeneficiaryDB.purchase_id == purchase.id)
        .all()
    )
    buyer = db.query(UserDB).filter(UserDB.user_id == purchase.buyer_id).first()
    return {
        "id": purchase.id,
        "event_id": purchase.event_id,
        "buyer": {
            "user_id": buyer.user_id,
            "first_name": buyer.first_name,
            "last_name": buyer.last_name,
        }
        if buyer
        else None,
        "description": purchase.description,
        "amount": float(purchase.amount),
        "receipt_photo_url": purchase.receipt_photo_url,
        "created_at": purchase.created_at.isoformat() if purchase.created_at else None,
        "beneficiaries": [
            {
                "user_id": u.user_id,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "share_amount": float(b.share_amount),
            }
            for b, u in beneficiaries
        ],
    }
