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
