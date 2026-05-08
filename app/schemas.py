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


class FriendRequest(BaseModel):
    user_id: str
    friend_id: str
