from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infrastructure.db import GameEventModel


class EventRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def append(self, event: GameEventModel) -> GameEventModel:
        self._db.add(event)
        self._db.flush()
        return event

    def next_seq(self, game_id: str) -> int:
        max_seq = self._db.execute(
            select(func.max(GameEventModel.seq)).where(GameEventModel.game_id == game_id)
        ).scalar_one()
        return int(max_seq or 0) + 1

    def list_after(self, game_id: str, after_seq: int = 0) -> list[GameEventModel]:
        return self._db.execute(
            select(GameEventModel)
            .where(GameEventModel.game_id == game_id, GameEventModel.seq > after_seq)
            .order_by(GameEventModel.seq.asc())
        ).scalars().all()
