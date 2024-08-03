from model.base import Base
from sqlalchemy import String
from sqlalchemy.orm import mapped_column

class Category(Base):
    __tablename__ = "category"
    id = mapped_column(String(10), primary_key=True)
    name = mapped_column(String(100),nullable=False)