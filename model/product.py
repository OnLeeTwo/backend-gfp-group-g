from model.base import Base
from sqlalchemy.orm import mapped_column
from sqlalchemy import String, Float, Integer, Boolean, DateTime

from sqlalchemy.sql import func

class Product(Base):
    __tablename__ = 'product'


    id = mapped_column(String(10), primary_key=True)
    market_id = mapped_column(String(10), nullable=False)
    name =  mapped_column(String(100), nullable=False)
    price =  mapped_column(String(10), nullable=False)
    category_id =  mapped_column(Float, nullable=False)
    stock =  mapped_column(Integer, nullable=False)
    images =  mapped_column(String(100), nullable=False)
    is_premium =  mapped_column(Boolean, default=False)
    is_deleted = mapped_column(Integer, default=0)
    time_deleted = mapped_column(DateTime(timezone=True))
    created_at = mapped_column(DateTime(timezone=True))
    created_by = mapped_column(String)
    updated_at = mapped_column(DateTime(timezone=True))
    updated_by = mapped_column(DateTime(timezone=True))