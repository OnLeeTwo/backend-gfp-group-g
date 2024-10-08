from model.base import Base

from sqlalchemy.orm import mapped_column
from sqlalchemy import String


class Seller(Base):
    __tablename__ = "seller"

    seller_id = mapped_column(String(10), primary_key=True)
    user_id = mapped_column(String(10), nullable=False)

