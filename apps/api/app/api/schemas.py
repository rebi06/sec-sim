from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class DefenseType(str, Enum):
    FORTIFY = 'fortify'
    MONITOR = 'monitor'
    RECOVER = 'recover'


class GameCreateResponse(BaseModel):
    id: str
    status: str
    ruleset_version: str
    turn_number: int
    max_turns: int
    state: dict[str, Any]


class GameResponse(GameCreateResponse):
    pass


class PlayTurnRequest(BaseModel):
    defense: DefenseType


class EventResponse(BaseModel):
    id: str
    seq: int
    event_type: str
    actor: str
    payload: dict[str, Any]
    correlation_id: Optional[str] = None
    created_at: str
