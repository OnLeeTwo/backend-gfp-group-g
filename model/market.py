from sqlalchemy.sql import func 
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import mapped_column
from model.base import Base

class Market(Base):
    __tablename__ = "market"

    market_id = mapped_column(String(10), primary_key=True)
    seller_id = mapped_column(String(10), ForeignKey('seller.seller_id'), nullable=False)
    name = mapped_column(String(255), nullable=False)
    location = mapped_column(Text, nullable=True)
    created_at = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_by = mapped_column(Integer, nullable=False)
    updated_at = mapped_column(DateTime, onupdate=func.now())
    updated_by = mapped_column(Integer, nullable=True)
    profile_picture = mapped_column(Text, nullable=True)

