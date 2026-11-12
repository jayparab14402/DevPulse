from datetime import datetime

from sqlalchemy import (
    Boolean,
    Enum,
    Float,
    ForeignKey,
    Identity,
    Integer,
    String,
    Text,
    TIMESTAMP,
    func,
)

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .enums import ErrorLevel, MonitorStatus


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


class Monitor(Base):
    __tablename__ = "monitors"

    id: Mapped[int] = mapped_column(
        Integer,
        Identity(always=False),
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    url: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    method: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="GET"
    )

    expected_status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=200
    )

    timeout_seconds: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=5
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False
    )

    checks: Mapped[list["MonitorCheck"]] = relationship(
        back_populates="monitor"
    )


class MonitorCheck(Base):
    __tablename__ = "monitor_checks"

    id: Mapped[int] = mapped_column(
        Integer,
        Identity(always=False),
        primary_key=True
    )

    monitor_id: Mapped[int] = mapped_column(
        ForeignKey("monitors.id"),
        nullable=False
    )

    status: Mapped[MonitorStatus] = mapped_column(
        Enum(MonitorStatus, name="monitor_status"),
        nullable=False
    )

    http_status: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    latency_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    checked_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False
    )

    monitor: Mapped["Monitor"] = relationship(
        back_populates="checks"
    )