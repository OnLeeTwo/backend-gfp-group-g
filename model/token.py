from model.base import Base

from sqlalchemy.orm import mapped_column
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.sql import func


class TokenBlocklist(Base):
    __tablename__ = "token_blocklist"

    id = mapped_column(Integer, primary_key=True)
    jti = mapped_column(String, nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
