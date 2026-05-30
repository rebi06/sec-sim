from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, Optional
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, create_engine, select
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker
from sqlalchemy.types import JSON, TypeDecorator


class GUID(TypeDecorator):
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PGUUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value


class Base(DeclarativeBase):
    pass


JsonType = JSONB().with_variant(JSON(), 'sqlite')


class GameSessionModel(Base):
    __tablename__ = 'game_sessions'

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid4()))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='active')
    ruleset_version: Mapped[str] = mapped_column(String(40), nullable=False, default='v1')
    seed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    max_turns: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    integrity: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    posture: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    alert: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    winner: Mapped[str] = mapped_column(String(20), nullable=False, default='none')
    status_flags: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    events: Mapped[list['GameEventModel']] = relationship(back_populates='game', cascade='all, delete-orphan')


class GameEventModel(Base):
    __tablename__ = 'game_events'

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid4()))
    game_id: Mapped[str] = mapped_column(GUID(), ForeignKey('game_sessions.id'), nullable=False, index=True)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    actor: Mapped[str] = mapped_column(String(20), nullable=False)
    payload: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    causation_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    game: Mapped[GameSessionModel] = relationship(back_populates='events')


def get_database_url() -> str:
    return os.getenv('DATABASE_URL', 'sqlite:///./sec_sim.db')


engine = create_engine(get_database_url(), future=True, echo=False)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
