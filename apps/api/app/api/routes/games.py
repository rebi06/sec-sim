from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.schemas import EventResponse, GameCreateResponse, GameResponse, PlayTurnRequest
from app.application.service import GameService
from app.domain.entities import DefenseType
from app.infrastructure.db import get_session

router = APIRouter(prefix='/api/games', tags=['games'])


def get_db() -> Session:
    with get_session() as session:
        yield session


@router.post('', response_model=GameCreateResponse)
def create_game(db: Session = Depends(get_db)):
    service = GameService(db)
    return service.create_game()


@router.get('/{game_id}', response_model=GameResponse)
def get_game(game_id: str, db: Session = Depends(get_db)):
    service = GameService(db)
    try:
        return service.get_game(game_id)
    except KeyError:
        raise HTTPException(status_code=404, detail='game not found')


@router.post('/{game_id}/actions/defend', response_model=GameResponse)
def play_turn(game_id: str, payload: PlayTurnRequest, db: Session = Depends(get_db)):
    service = GameService(db)
    try:
        return service.play_turn(game_id, DefenseType(payload.defense.value))
    except KeyError:
        raise HTTPException(status_code=404, detail='game not found')


@router.get('/{game_id}/events', response_model=list[EventResponse])
def list_events(game_id: str, after_seq: int = Query(default=0, ge=0), db: Session = Depends(get_db)):
    service = GameService(db)
    try:
        return service.list_events(game_id, after_seq=after_seq)
    except KeyError:
        raise HTTPException(status_code=404, detail='game not found')
