from __future__ import annotations

from typing import Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.domain.entities import AttackType, DefenseType, EventType, GameState, GameStatus, Winner
from app.domain.rules import RuleEngine
from app.infrastructure.db import GameEventModel, GameSessionModel
from app.infrastructure.repositories.event_repo import EventRepository
from app.infrastructure.repositories.game_repo import GameRepository


class GameService:
    def __init__(self, db: Session, rules: Optional[RuleEngine] = None) -> None:
        self._games = GameRepository(db)
        self._events = EventRepository(db)
        self.rules = rules or RuleEngine()

    def create_game(self) -> dict:
        game = self._games.create(GameSessionModel(
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
        ))
        correlation_id = str(uuid4())
        self._emit(game.id, EventType.GAME_STARTED, 'system', {
            'turn_number': 1,
            'integrity': 100,
            'posture': 100,
            'alert': 0,
        }, correlation_id=correlation_id)
        return self._serialize_game(game)

    def get_game(self, game_id: str) -> dict:
        game = self._games.get(game_id)
        if not game:
            raise KeyError('game not found')
        return self._serialize_game(game)

    def list_events(self, game_id: str, after_seq: int = 0) -> list[dict]:
        if not self._games.get(game_id):
            raise KeyError('game not found')
        rows = self._events.list_after(game_id, after_seq)
        return [self._serialize_event(e) for e in rows]

    def play_turn(self, game_id: str, defense: DefenseType) -> dict:
        game = self._games.get(game_id)
        if not game:
            raise KeyError('game not found')
        if game.status == 'finished':
            return self._serialize_game(game)

        state = self._load_state(game)
        correlation_id = str(uuid4())

        attack = self.rules.choose_ai_attack(state)
        result = self.rules.resolve(state, defense, attack)
        self.rules.apply_resolution(state, result)

        self._emit(game.id, EventType.DEFENSE_CHOSEN, 'player',
                   {'defense': defense.value, 'turn': state.turn_number},
                   correlation_id=correlation_id)
        self._emit(game.id, EventType.ATTACK_CHOSEN, 'ai',
                   {'attack': attack.value, 'turn': state.turn_number},
                   correlation_id=correlation_id)
        self._emit(game.id, EventType.RESOLUTION_APPLIED, 'system', {
            'attack': attack.value,
            'defense': defense.value,
            'delta_integrity': result.delta_integrity,
            'delta_posture': result.delta_posture,
            'delta_alert': result.delta_alert,
            'notes': result.notes,
            'state': self._state_payload(state),
        }, correlation_id=correlation_id)

        state.turn_number += 1
        self.rules.finalize(state)

        if state.status == GameStatus.FINISHED:
            self._emit(game.id, EventType.GAME_ENDED, 'system',
                       {'winner': state.winner.value, 'reason': self._terminal_reason(state)},
                       correlation_id=correlation_id)
        else:
            self._emit(game.id, EventType.TURN_ADVANCED, 'system',
                       {'next_turn': state.turn_number},
                       correlation_id=correlation_id)

        self._save_state(game, state)
        return self._serialize_game(game)

    # ------------------------------------------------------------------ #

    def _emit(self, game_id: str, event_type: EventType, actor: str, payload: dict,
              correlation_id: str, causation_id: Optional[str] = None) -> None:
        seq = self._events.next_seq(game_id)
        self._events.append(GameEventModel(
            game_id=game_id,
            seq=seq,
            event_type=event_type.value,
            actor=actor,
            payload=payload,
            correlation_id=correlation_id,
            causation_id=causation_id,
        ))

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
        game.status = state.status.value
        game.winner = state.winner.value
        game.status_flags = state.status_flags
        self._games.save(game)

    def _terminal_reason(self, state: GameState) -> str:
        if state.alert >= 100:
            return 'alert_threshold'
        if state.integrity <= 0 or state.posture <= 0:
            return 'resource_exhaustion'
        if state.turn_number > state.max_turns:
            return 'survived_max_turns'
        return 'unknown'

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
            'correlation_id': event.correlation_id,
            'created_at': event.created_at.isoformat(),
        }

    def _state_payload(self, state: GameState) -> dict:
        return {
            'integrity': state.integrity,
            'posture': state.posture,
            'alert': state.alert,
            'turn_number': state.turn_number,
            'status': state.status.value,
            'winner': state.winner.value,
        }
