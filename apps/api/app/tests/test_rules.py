from app.domain.entities import AttackType, DefenseType, GameState, GameStatus, Winner
from app.domain.rules import RuleEngine


def test_ai_attack_changes_by_state():
    engine = RuleEngine()
    assert engine.choose_ai_attack(GameState(integrity=20)) == AttackType.RESOURCE_DRAIN
    assert engine.choose_ai_attack(GameState(alert=80)) == AttackType.CONFUSION


def test_resolution_changes_state():
    engine = RuleEngine()
    state = GameState()
    result = engine.resolve(state, DefenseType.MONITOR, AttackType.RECON_PRESSURE)
    engine.apply_resolution(state, result)
    assert state.alert < 100
    assert state.posture <= 100


def test_integrity_zero_triggers_ai_win():
    engine = RuleEngine()
    state = GameState(integrity=0, turn_number=2)
    engine.finalize(state)
    assert state.status == GameStatus.FINISHED
    assert state.winner == Winner.AI


def test_posture_zero_triggers_ai_win():
    engine = RuleEngine()
    state = GameState(posture=0, turn_number=2)
    engine.finalize(state)
    assert state.winner == Winner.AI


def test_alert_max_triggers_ai_win():
    engine = RuleEngine()
    state = GameState(alert=100, turn_number=2)
    engine.finalize(state)
    assert state.winner == Winner.AI


def test_survive_max_turns_triggers_player_win():
    engine = RuleEngine()
    state = GameState(turn_number=11, max_turns=10)
    engine.finalize(state)
    assert state.status == GameStatus.FINISHED
    assert state.winner == Winner.PLAYER


def test_active_game_has_no_winner():
    engine = RuleEngine()
    state = GameState(integrity=50, posture=50, alert=50, turn_number=5)
    engine.finalize(state)
    assert state.status == GameStatus.ACTIVE
    assert state.winner == Winner.NONE


def test_state_clamp():
    state = GameState(integrity=200, posture=-10, alert=150)
    state.clamp()
    assert state.integrity == 100
    assert state.posture == 0
    assert state.alert == 100


def test_resolution_result_has_notes():
    engine = RuleEngine()
    state = GameState()
    result = engine.resolve(state, DefenseType.FORTIFY, AttackType.RESOURCE_DRAIN)
    assert len(result.notes) > 0
