from sqlalchemy import String, DECIMAL, DateTime, Date, func
from sqlalchemy.orm import mapped_column
from model.base import Base


class Promotion(Base):
    __tablename__ = "promotions"

    promotion_id = mapped_column(String(10), primary_key=True)
    market_id = mapped_column(String(10), nullable=False)
    code = mapped_column(String(255), unique=True, nullable=False)
    discount_value = mapped_column(DECIMAL, nullable=False)
    created_by=mapped_column(String(10))
    created_at = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    start_date = mapped_column(Date, nullable=False)
    end_date = mapped_column(Date, nullable=False)
