from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    link: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    link: str | None = None
    photo_url: str | None = None


class FriendRequest(BaseModel):
    user_id: str
    friend_id: str


class FriendRespond(BaseModel):
    user_id: str
    friend_id: str
    action: str


class EventCreate(BaseModel):
    creator_id: str
    title: str
    deadline: datetime | None = None
    participant_ids: list[str] = []
    guest_names: list[str] = []


class EventUpdate(BaseModel):
    title: str | None = None
    deadline: datetime | None = None


class ParticipantAdd(BaseModel):
    user_id: str


class GuestCreate(BaseModel):
    name: str


class PurchaseCreate(BaseModel):
    buyer_id: str
    description: str
    amount: float
    receipt_photo_url: str | None = None
    beneficiary_ids: list[str] = []


class PurchaseUpdate(BaseModel):
    description: str | None = None
    amount: float | None = None
    beneficiary_ids: list[str] | None = None


class DebtCreate(BaseModel):
    creditor_id: str
    debtor_id: str
    amount: float
    description: str | None = None
    deadline: datetime | None = None
    photo_url: str | None = None


class DebtUpdate(BaseModel):
    status: str | None = None
    payment_photo_url: str | None = None


class EventConfirmRequest(BaseModel):
    user_id: str
