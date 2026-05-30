from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class GameStatus(str, Enum):
    ACTIVE = 'active'
    FINISHED = 'finished'


class Winner(str, Enum):
    PLAYER = 'player'
    AI = 'ai'
    NONE = 'none'


class AttackType(str, Enum):
    RECON_PRESSURE = 'recon_pressure'
    RESOURCE_DRAIN = 'resource_drain'
    CONFUSION = 'confusion'


class DefenseType(str, Enum):
    FORTIFY = 'fortify'
    MONITOR = 'monitor'
    RECOVER = 'recover'


class EventType(str, Enum):
    GAME_STARTED = 'game_started'
    DEFENSE_CHOSEN = 'defense_chosen'
    ATTACK_CHOSEN = 'attack_chosen'
    RESOLUTION_APPLIED = 'resolution_applied'
    TURN_ADVANCED = 'turn_advanced'
    GAME_ENDED = 'game_ended'


@dataclass
class GameState:
    integrity: int = 100
    posture: int = 100
    alert: int = 0
    turn_number: int = 1
    max_turns: int = 10
    status: GameStatus = GameStatus.ACTIVE
    winner: Winner = Winner.NONE
    status_flags: dict[str, Any] = field(default_factory=dict)

    def clamp(self) -> None:
        self.integrity = max(0, min(100, self.integrity))
        self.posture = max(0, min(100, self.posture))
        self.alert = max(0, min(100, self.alert))

    def is_terminal(self) -> bool:
        return self.status == GameStatus.FINISHED


@dataclass
class GameEvent:
    event_type: EventType
    actor: str
    payload: dict[str, Any]
    seq: int = 0
    id: UUID = field(default_factory=uuid4)
