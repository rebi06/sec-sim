from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.domain.judge import judge
from app.infrastructure.scenario_loader import load_all, load_by_id

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


class ScenarioSummary(BaseModel):
    id: str
    title: str
    category: str
    difficulty: str
    service_name: str


class HintResponse(BaseModel):
    level1: str
    level2: str
    level3: str


class ScenarioDetail(BaseModel):
    id: str
    title: str
    category: str
    difficulty: str
    service_name: str
    description: str
    vulnerable_code: str
    hint: HintResponse


class SubmitRequest(BaseModel):
    code: str
    hint_used: int = 0  # 使ったヒントレベル（0=なし）


class TestResultResponse(BaseModel):
    test_id: str
    description: str
    passed: bool
    reason: str


class SubmitResponse(BaseModel):
    passed: bool
    score: int
    feedback: str
    test_results: List[TestResultResponse]
    explanation: Optional[str] = None


@router.get("", response_model=List[ScenarioSummary])
def list_scenarios():
    return [
        ScenarioSummary(
            id=s.id,
            title=s.title,
            category=s.category,
            difficulty=s.difficulty,
            service_name=s.service_name,
        )
        for s in load_all()
    ]


@router.get("/{scenario_id}", response_model=ScenarioDetail)
def get_scenario(scenario_id: str):
    scenario = load_by_id(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="scenario not found")
    return ScenarioDetail(
        id=scenario.id,
        title=scenario.title,
        category=scenario.category,
        difficulty=scenario.difficulty,
        service_name=scenario.service_name,
        description=scenario.description,
        vulnerable_code=scenario.vulnerable_code,
        hint=HintResponse(
            level1=scenario.hint.level1,
            level2=scenario.hint.level2,
            level3=scenario.hint.level3,
        ),
    )


@router.post("/{scenario_id}/submit", response_model=SubmitResponse)
def submit(scenario_id: str, payload: SubmitRequest):
    scenario = load_by_id(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="scenario not found")
    result = judge(payload.code, scenario)
    return SubmitResponse(
        passed=result.passed,
        score=result.score,
        feedback=result.feedback,
        test_results=[
            TestResultResponse(
                test_id=r.test_id,
                description=r.description,
                passed=r.passed,
                reason=r.reason,
            )
            for r in result.test_results
        ],
        explanation=scenario.explanation if result.passed else None,
    )
