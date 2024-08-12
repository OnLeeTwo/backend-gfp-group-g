from sqlalchemy import String, Integer, Float
from sqlalchemy.orm import mapped_column
from model.base import Base


class OrderDetails(Base):
    __tablename__ = "order_details"

    order_details_id = mapped_column(String(10), primary_key=True)
    order_id = mapped_column(String(10), nullable=True)
    user_id = mapped_column(String(10), nullable=False)
    product_id = mapped_column(String(10), nullable=False)
    quantity = mapped_column(Integer, nullable=False)
    total_price = mapped_column(Float, nullable=False)
