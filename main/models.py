from datetime import datetime, date
import asyncio  # noqa: F401
from enum import unique

from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import String, Text, DateTime, BigInteger, Date, Float, Boolean
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    pass


class Announcement(Base):
    __tablename__ = "announcement"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    date_added: Mapped[date] = mapped_column(Date, server_default=func.now())
    publication_date: Mapped[date] = mapped_column(Date, nullable=True)
    title: Mapped[str] = mapped_column(String(500))
    price: Mapped[float] = mapped_column(Float, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    # region_id: Mapped[int]
    # seller_id: Mapped[int]
    url: Mapped[str] = mapped_column(Text, nullable=True, unique=True)
    status: Mapped[bool] = mapped_column(Boolean, nullable=True)
    # category_id: Mapped[int]


class BotUser(Base):
    __tablename__ = "bot_user"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)