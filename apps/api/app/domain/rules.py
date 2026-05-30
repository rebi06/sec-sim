from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .entities import AttackType, DefenseType, GameState, Winner, GameStatus


@dataclass
class ResolutionResult:
    attack: AttackType
    defense: DefenseType
    delta_integrity: int
    delta_posture: int
    delta_alert: int
    notes: list[str]


class RuleEngine:
    def choose_ai_attack(self, state: GameState) -> AttackType:
        if state.integrity <= 35:
            return AttackType.RESOURCE_DRAIN
        if state.alert >= 70:
            return AttackType.CONFUSION
        if state.turn_number % 3 == 1:
            return AttackType.RECON_PRESSURE
        if state.turn_number % 3 == 2:
            return AttackType.RESOURCE_DRAIN
        return AttackType.CONFUSION

    def resolve(self, state: GameState, defense: DefenseType, attack: AttackType) -> ResolutionResult:
        base = {
            AttackType.RECON_PRESSURE: {'integrity': 0, 'posture': -8, 'alert': 18},
            AttackType.RESOURCE_DRAIN: {'integrity': -16, 'posture': 0, 'alert': 8},
            AttackType.CONFUSION: {'integrity': 0, 'posture': -14, 'alert': 12},
        }[attack]
        defense_effects = {
            DefenseType.FORTIFY: {'integrity': 4, 'posture': 12, 'alert': -2, 'mitigation': 0.35, 'note': 'strengthened posture'},
            DefenseType.MONITOR: {'integrity': 0, 'posture': 2, 'alert': -8, 'mitigation': 0.55, 'note': 'reduced attack impact'},
            DefenseType.RECOVER: {'integrity': 10, 'posture': -2, 'alert': -10, 'mitigation': 0.15, 'note': 'restored resources'},
        }[defense]

        mitigation = defense_effects['mitigation']
        delta_integrity = round(base['integrity'] * (1 - mitigation) + defense_effects['integrity'])
        delta_posture = round(base['posture'] * (1 - mitigation) + defense_effects['posture'])
        delta_alert = round(base['alert'] * (1 - mitigation) + defense_effects['alert'])

        notes = [
            f'{defense.value} applied',
            defense_effects['note'],
            f'{attack.value} resolved',
        ]
        return ResolutionResult(
            attack=attack,
            defense=defense,
            delta_integrity=delta_integrity,
            delta_posture=delta_posture,
            delta_alert=delta_alert,
            notes=notes,
        )

    def apply_resolution(self, state: GameState, result: ResolutionResult) -> GameState:
        state.integrity += result.delta_integrity
        state.posture += result.delta_posture
        state.alert += result.delta_alert
        state.clamp()
        return state

    def check_winner(self, state: GameState) -> Winner:
        if state.integrity <= 0 or state.posture <= 0 or state.alert >= 100:
            return Winner.AI
        if state.turn_number > state.max_turns:
            return Winner.PLAYER
        return Winner.NONE

    def finalize(self, state: GameState) -> GameState:
        winner = self.check_winner(state)
        if winner != Winner.NONE:
            state.status = GameStatus.FINISHED
            state.winner = winner
        return state
