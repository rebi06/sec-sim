from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.entities import AttackType, DefenseType, EventType, GameEvent, GameState, GameStatus, Winner
from app.domain.rules import RuleEngine
from app.infrastructure.db import GameEventModel, GameSessionModel


class GameService:
    def __init__(self, db: Session, rules: RuleEngine | None = None) -> None:
        self.db = db
        self.rules = rules or RuleEngine()

    def create_game(self) -> dict:
        game = GameSessionModel(
            id=str(uuid4()),
            status='active',
            ruleset_version='v1',
            seed=0,
            turn_number=1,
            max_turns=10,
            integrity=100,
            posture=100,
            alert=0,
            winner='none',
            status_flags={},
        )
        self.db.add(game)
        self.db.flush()
        self._append_event(game.id, 1, EventType.GAME_STARTED, 'system', {
            'turn_number': 1,
            'integrity': 100,
            'posture': 100,
            'alert': 0,
        })
        return self._serialize_game(game)

    def get_game(self, game_id: str) -> dict:
        game = self.db.get(GameSessionModel, game_id)
        if not game:
            raise KeyError('game not found')
        return self._serialize_game(game)

    def list_events(self, game_id: str, after_seq: int = 0) -> list[dict]:
        rows = self.db.execute(
            select(GameEventModel).where(GameEventModel.game_id == game_id, GameEventModel.seq > after_seq).order_by(GameEventModel.seq.asc())
        ).scalars().all()
        return [self._serialize_event(row) for row in rows]

    def play_turn(self, game_id: str, defense: DefenseType) -> dict:
        game = self.db.get(GameSessionModel, game_id)
        if not game:
            raise KeyError('game not found')
        if game.status == 'finished':
            return self._serialize_game(game)

        state = self._load_state(game)
        current_seq = self._next_seq(game_id)

        self._append_event(game_id, current_seq, EventType.DEFENSE_CHOSEN, 'player', {'defense': defense.value, 'turn': state.turn_number})
        attack = self.rules.choose_ai_attack(state)
        self._append_event(game_id, current_seq + 1, EventType.ATTACK_CHOSEN, 'ai', {'attack': attack.value, 'turn': state.turn_number})
        result = self.rules.resolve(state, defense, attack)
        self.rules.apply_resolution(state, result)
        self._append_event(game_id, current_seq + 2, EventType.RESOLUTION_APPLIED, 'system', {
            'attack': attack.value,
            'defense': defense.value,
            'delta_integrity': result.delta_integrity,
            'delta_posture': result.delta_posture,
            'delta_alert': result.delta_alert,
            'notes': result.notes,
            'state': self._state_payload(state),
        })

        state.turn_number += 1
        self.rules.finalize(state)
        if state.status == GameStatus.FINISHED:
            self._append_event(game_id, current_seq + 3, EventType.GAME_ENDED, 'system', {'winner': state.winner.value, 'reason': self._terminal_reason(state)})
        else:
            self._append_event(game_id, current_seq + 3, EventType.TURN_ADVANCED, 'system', {'next_turn': state.turn_number})

        self._save_state(game, state)
        return self._serialize_game(game)

    def _terminal_reason(self, state: GameState) -> str:
        if state.alert >= 100:
            return 'alert_threshold'
        if state.integrity <= 0 or state.posture <= 0:
            return 'resource_exhaustion'
        if state.turn_number > state.max_turns:
            return 'survived_max_turns'
        return 'unknown'

    def _load_state(self, game: GameSessionModel) -> GameState:
        return GameState(
            integrity=game.integrity,
            posture=game.posture,
            alert=game.alert,
            turn_number=game.turn_number,
            max_turns=game.max_turns,
            status=GameStatus(game.status),
            winner=Winner(game.winner),
            status_flags=dict(game.status_flags or {}),
        )

    def _save_state(self, game: GameSessionModel, state: GameState) -> None:
        game.integrity = state.integrity
        game.posture = state.posture
        game.alert = state.alert
        game.turn_number = state.turn_number
        game.max_turns = state.max_turns
        game.status = state.status.value
        game.winner = state.winner.value
        game.status_flags = state.status_flags
        if game.status == 'finished' and game.finished_at is None:
            game.finished_at = datetime.now(timezone.utc)
        self.db.add(game)
        self.db.flush()

    def _append_event(self, game_id: str, seq: int, event_type: EventType, actor: str, payload: dict) -> None:
        event = GameEventModel(
            game_id=game_id,
            seq=seq,
            event_type=event_type.value,
            actor=actor,
            payload=payload,
            correlation_id=str(uuid4()),
            causation_id=None,
        )
        self.db.add(event)
        self.db.flush()

    def _next_seq(self, game_id: str) -> int:
        max_seq = self.db.execute(select(func.max(GameEventModel.seq)).where(GameEventModel.game_id == game_id)).scalar_one()
        return int(max_seq or 0) + 1

    def _serialize_game(self, game: GameSessionModel) -> dict:
        return {
            'id': game.id,
            'status': game.status,
            'ruleset_version': game.ruleset_version,
            'turn_number': game.turn_number,
            'max_turns': game.max_turns,
            'state': {
                'integrity': game.integrity,
                'posture': game.posture,
                'alert': game.alert,
                'status_flags': game.status_flags or {},
                'winner': game.winner,
            },
        }

    def _serialize_event(self, event: GameEventModel) -> dict:
        return {
            'id': event.id,
            'seq': event.seq,
            'event_type': event.event_type,
            'actor': event.actor,
            'payload': event.payload,
            'created_at': event.created_at.isoformat(),
        }

    def _state_payload(self, state: GameState) -> dict:
        return {
            'integrity': state.integrity,
            'posture': state.posture,
            'alert': state.alert,
            'turn_number': state.turn_number,
            'max_turns': state.max_turns,
            'status': state.status.value,
            'winner': state.winner.value,
            'status_flags': state.status_flags,
        }
