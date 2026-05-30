from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TestCase:
    id: str
    description: str
    type: str  # code_contains | code_not_contains
    expect: str  # pass | blocked
    required: Optional[str] = None
    forbidden: Optional[str] = None


@dataclass
class Hint:
    level1: str
    level2: str
    level3: str


@dataclass
class Scenario:
    id: str
    title: str
    category: str
    difficulty: str
    service_name: str
    description: str
    vulnerable_code: str
    fixed_code: str
    test_cases: List[TestCase]
    correct_concepts: List[str]
    hint: Hint
    explanation: str
