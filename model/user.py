from model.base import Base

from sqlalchemy.sql import func
from sqlalchemy import String, DateTime, Enum, Boolean
from sqlalchemy.orm import mapped_column
import bcrypt


class User(Base):
    __tablename__ = "users"

    user_id = mapped_column(String(10), primary_key=True)
    email = mapped_column(String(100), nullable=False)
    password_hash = mapped_column(String(255), nullable=False)
    role = mapped_column(Enum("buyer", "seller", name="role"), nullable=False)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_deleted = mapped_column(Boolean(default=False))
    time_deleted = mapped_column(DateTime(timezone=True), nullable=True)
    profile_picture = mapped_column(String(255), nullable=True)

    def set_password(self, password_hash):
        self.password_hash = bcrypt.hashpw(
            password_hash.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password_hash):
        return bcrypt.checkpw(
            password_hash.encode("utf-8"), self.password_hash.encode("utf-8")
        )
