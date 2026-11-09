from datetime import datetime

from sqlalchemy import Enum, Identity, Integer, String, Text, TIMESTAMP, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .enums import ErrorLevel


class Base(DeclarativeBase):
    pass


class ErrorEvent(Base):
    __tablename__ = "error_events"
    id: Mapped[int] = mapped_column(
        Integer,
        Identity(always=False),
        primary_key=True,
    )
    service: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    level: Mapped[ErrorLevel] = mapped_column(
        Enum(
            ErrorLevel,
            name="error_level",
        ),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
    )