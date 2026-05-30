from app.domain.entities import AttackType, DefenseType, GameState
from app.domain.rules import RuleEngine


def test_ai_attack_changes_by_state():
    engine = RuleEngine()
    assert engine.choose_ai_attack(GameState(integrity=20)).value == AttackType.RESOURCE_DRAIN.value
    assert engine.choose_ai_attack(GameState(alert=80)).value == AttackType.CONFUSION.value


def test_resolution_changes_state():
    engine = RuleEngine()
    state = GameState()
    result = engine.resolve(state, DefenseType.MONITOR, AttackType.RECON_PRESSURE)
    engine.apply_resolution(state, result)
    assert state.alert < 100
    assert state.posture <= 100
