from model.base import Base

from sqlalchemy.orm import mapped_column
from sqlalchemy import Integer, String


class Seller(Base):
    __tablename__ = "seller"

    seller_id = mapped_column(Integer, primary_key=True)
    user_id = mapped_column(String(10), nullable=False)