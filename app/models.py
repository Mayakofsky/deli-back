import secrets
import string

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.sql import func

from app.database import Base


def generate_custom_id():
    return "USR-" + "".join(
        secrets.choice(string.ascii_uppercase + string.digits) for _ in range(5)
    )


class UserDB(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, default=generate_custom_id, unique=True)
    email = Column(String, unique=True, nullable=True, index=True)
    password = Column(String, nullable=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=True)
    link = Column(String, nullable=True)
    is_guest = Column(Boolean, default=False)
    photo_url = Column(String, nullable=True)


class FriendshipDB(Base):
    __tablename__ = "friendships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    friend_id = Column(
        String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    status = Column(String, default="pending", nullable=False)


class EventDB(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=generate_custom_id)
    creator_id = Column(
        String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String, nullable=False)
    deadline = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EventParticipantDB(Base):
    __tablename__ = "event_participants"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(
        String, ForeignKey("events.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    joined_at = Column(DateTime(timezone=True), server_default=func.now())


class EventPurchaseDB(Base):
    __tablename__ = "event_purchases"

    id = Column(String, primary_key=True, default=generate_custom_id)
    event_id = Column(
        String, ForeignKey("events.id", ondelete="CASCADE"), nullable=False
    )
    buyer_id = Column(
        String, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    description = Column(String, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    receipt_photo_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PurchaseBeneficiaryDB(Base):
    __tablename__ = "purchase_beneficiaries"

    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(
        String, ForeignKey("event_purchases.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    share_amount = Column(Numeric(10, 2), nullable=False)


class DebtDB(Base):
    __tablename__ = "debts"

    id = Column(String, primary_key=True, default=generate_custom_id)
    creditor_id = Column(
        String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    debtor_id = Column(
        String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    amount = Column(Numeric(10, 2), nullable=False)
    description = Column(String, nullable=True)
    deadline = Column(DateTime(timezone=True), nullable=True)
    photo_url = Column(String, nullable=True)
    payment_photo_url = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class EventConfirmationDB(Base):
    __tablename__ = "event_confirmations"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(
        String, ForeignKey("events.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
