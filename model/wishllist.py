from model.base import Base
from sqlalchemy import String
from sqlalchemy.orm import mapped_column


class Wishlist(Base):
    __tablename__ = "wishlist"

    id = mapped_column(String(10), primary_key=True, nullable=False)
    user_id = mapped_column(String(10), nullable=False)
    product_id = mapped_column(String(10), nullable=False)
