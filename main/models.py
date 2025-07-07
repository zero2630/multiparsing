from datetime import datetime, date
import asyncio  # noqa: F401
from enum import unique

from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import String, Text, DateTime, BigInteger, Date, Float, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    pass


class Announcement(Base):
    __tablename__ = "announcement"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    # publication_date: Mapped[date] = mapped_column(Date, nullable=True)
    publication_date: Mapped[str] = mapped_column(String(100), nullable=True)
    title: Mapped[str] = mapped_column(String(500))
    price: Mapped[float] = mapped_column(Float, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    # region_id: Mapped[int]
    # seller_id: Mapped[int]
    url: Mapped[str] = mapped_column(Text, nullable=True, unique=True)
    img_url: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(15), nullable=True)
    # category_id: Mapped[int]
    created_at: Mapped[date] = mapped_column(Date, server_default=func.now())


class ParserTask(Base):
    __tablename__ = "parser_task"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    search_query: Mapped[dict] = mapped_column(JSONB, unique=True)
    periodicity: Mapped[int]
    status: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[date] = mapped_column(Date, server_default=func.now())


class UserToTask(Base):
    __tablename__ = "user_to_task"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("bot_user.telegram_id"))
    task_id: Mapped[int] = mapped_column(ForeignKey("parser_task.id"))
    uniq_val: Mapped[str] = mapped_column(String(50), unique=True)
    created_at: Mapped[date] = mapped_column(Date, server_default=func.now())


class AnnouncementToTask(Base):
    __tablename__ = "announcement_to_task"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    announcement_id: Mapped[int] = mapped_column(ForeignKey("announcement.id"))
    task_id: Mapped[int] = mapped_column(ForeignKey("parser_task.id"))
    uniq_val: Mapped[str] = mapped_column(String(50), unique=True)
    created_at: Mapped[date] = mapped_column(Date, server_default=func.now())


class Viewed(Base):
    __tablename__ = "viewed"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    announcement_id: Mapped[int] = mapped_column(ForeignKey("announcement.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("bot_user.telegram_id"))
    created_at: Mapped[date] = mapped_column(Date, server_default=func.now())


class BotUser(Base):
    __tablename__ = "bot_user"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)