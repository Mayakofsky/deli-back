import secrets
import string

from sqlalchemy import Column, ForeignKey, Integer, String

from app.database import Base


def generate_custom_id():
    return "USR-" + "".join(
        secrets.choice(string.ascii_uppercase + string.digits) for _ in range(5)
    )


class UserDB(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, default=generate_custom_id, unique=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    link = Column(String, nullable=True)


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
