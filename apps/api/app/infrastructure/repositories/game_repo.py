from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db import GameSessionModel


class GameRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, model: GameSessionModel) -> GameSessionModel:
        self._db.add(model)
        self._db.flush()
        return model

    def get(self, game_id: str) -> Optional[GameSessionModel]:
        return self._db.get(GameSessionModel, game_id)

    def save(self, model: GameSessionModel) -> GameSessionModel:
        if model.status == 'finished' and model.finished_at is None:
            model.finished_at = datetime.now(timezone.utc)
        self._db.add(model)
        self._db.flush()
        return model
