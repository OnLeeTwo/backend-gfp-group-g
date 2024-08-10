from model.base import Base
from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import mapped_column

class Log(Base):
    __tablename__ = 'logs'

    id = mapped_column(Integer, primary_key=True)
    user_id=mapped_column(String(10), nullable=False)
    action=mapped_column(String)
    before=mapped_column(Text, nullable=True)
    after=mapped_column(Text, nullable=True)