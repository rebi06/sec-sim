from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List

import yaml

from app.domain.scenario import Hint, Scenario, TestCase

_SCENARIOS_DIR = Path(__file__).parent.parent.parent / "scenarios"
_cache: Dict[str, Scenario] = {}


def _parse(data: dict) -> Scenario:
    test_cases = [
        TestCase(
            id=tc["id"],
            description=tc["description"],
            type=tc["type"],
            expect=tc["expect"],
            required=tc.get("required"),
            forbidden=tc.get("forbidden"),
        )
        for tc in data.get("test_cases", [])
    ]
    hint_data = data.get("hint", {})
    return Scenario(
        id=data["id"],
        title=data["title"],
        category=data["category"],
        difficulty=data["difficulty"],
        service_name=data["service_name"],
        description=data["description"].strip(),
        vulnerable_code=data["vulnerable_code"].strip(),
        fixed_code=data["fixed_code"].strip(),
        test_cases=test_cases,
        correct_concepts=data.get("correct_concepts", []),
        hint=Hint(
            level1=hint_data.get("level1", ""),
            level2=hint_data.get("level2", ""),
            level3=hint_data.get("level3", ""),
        ),
        explanation=data.get("explanation", "").strip(),
    )


def load_all() -> List[Scenario]:
    scenarios = []
    for path in sorted(_SCENARIOS_DIR.glob("*.yaml")):
        scenario_id = path.stem
        if scenario_id not in _cache:
            with open(path, encoding="utf-8") as f:
                _cache[scenario_id] = _parse(yaml.safe_load(f))
        scenarios.append(_cache[scenario_id])
    return scenarios


def load_by_id(scenario_id: str) -> Scenario | None:
    if scenario_id in _cache:
        return _cache[scenario_id]
    path = _SCENARIOS_DIR / f"{scenario_id}.yaml"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        scenario = _parse(yaml.safe_load(f))
    _cache[scenario_id] = scenario
    return scenario
