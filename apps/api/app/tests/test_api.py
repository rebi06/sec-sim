from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_game_flow():
    created = client.post('/api/games')
    assert created.status_code == 200
    game_id = created.json()['id']

    fetched = client.get(f'/api/games/{game_id}')
    assert fetched.status_code == 200

    turn = client.post(f'/api/games/{game_id}/actions/defend', json={'defense': 'monitor'})
    assert turn.status_code == 200

    events = client.get(f'/api/games/{game_id}/events')
    assert events.status_code == 200
    assert len(events.json()) >= 4


def test_all_event_types_present_after_one_turn():
    res = client.post('/api/games')
    game_id = res.json()['id']
    client.post(f'/api/games/{game_id}/actions/defend', json={'defense': 'fortify'})
    events = client.get(f'/api/games/{game_id}/events').json()
    types = {e['event_type'] for e in events}
    assert 'game_started' in types
    assert 'defense_chosen' in types
    assert 'attack_chosen' in types
    assert 'resolution_applied' in types


def test_same_turn_events_share_correlation_id():
    res = client.post('/api/games')
    game_id = res.json()['id']
    client.post(f'/api/games/{game_id}/actions/defend', json={'defense': 'recover'})
    events = client.get(f'/api/games/{game_id}/events').json()
    turn_events = [e for e in events if e['event_type'] in ('defense_chosen', 'attack_chosen', 'resolution_applied')]
    correlation_ids = {e['correlation_id'] for e in turn_events}
    assert len(correlation_ids) == 1


def test_game_not_found_returns_404():
    assert client.get('/api/games/nonexistent').status_code == 404
    assert client.post('/api/games/nonexistent/actions/defend', json={'defense': 'monitor'}).status_code == 404


def test_finished_game_ignores_further_turns():
    res = client.post('/api/games')
    game_id = res.json()['id']
    for _ in range(12):
        client.post(f'/api/games/{game_id}/actions/defend', json={'defense': 'monitor'})
    game = client.get(f'/api/games/{game_id}').json()
    assert game['status'] == 'finished'
    turn_count_before = len(client.get(f'/api/games/{game_id}/events').json())
    client.post(f'/api/games/{game_id}/actions/defend', json={'defense': 'monitor'})
    turn_count_after = len(client.get(f'/api/games/{game_id}/events').json())
    assert turn_count_before == turn_count_after


def test_after_seq_filters_events():
    res = client.post('/api/games')
    game_id = res.json()['id']
    client.post(f'/api/games/{game_id}/actions/defend', json={'defense': 'fortify'})
    all_events = client.get(f'/api/games/{game_id}/events').json()
    assert len(all_events) > 0
    last_seq = all_events[-1]['seq']
    filtered = client.get(f'/api/games/{game_id}/events?after_seq={last_seq}').json()
    assert filtered == []
