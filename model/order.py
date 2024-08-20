from sqlalchemy import String, Integer, DECIMAL, DateTime, Enum, Text, ForeignKey, func
from sqlalchemy.orm import mapped_column
from model.base import Base
import enum


class OrderStatus(enum.Enum):
    pending = "Pending"
    shipping = "Shipping"
    delivered = "Delivered"
    arrived = "Arrived"
    cancelled = "Cancelled"


class PaymentStatus(enum.Enum):
    pending = "Pending"
    done = "Done"


class Order(Base):
    __tablename__ = "order"

    order_id = mapped_column(String(10), primary_key=True)
    user_id = mapped_column(String(10), ForeignKey("users.user_id"), nullable=False)
    total_amount = mapped_column(DECIMAL, nullable=False)
    tax = mapped_column(DECIMAL, nullable=False)
    shipping_fee = mapped_column(DECIMAL, nullable=False)
    admin_fee = mapped_column(DECIMAL, nullable=False)
    discount_fee = mapped_column(DECIMAL, nullable=True)
    created_at = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_by = mapped_column(Integer, nullable=False)
    status_order = mapped_column(Enum(OrderStatus), nullable=False)
    status_payment = mapped_column(Enum(PaymentStatus), nullable=False)
    shipping_address = mapped_column(Text, nullable=False)
    promotion_id = mapped_column(Integer, ForeignKey("promotions.promotion_id"))
