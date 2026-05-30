from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from app.domain.scenario import Scenario, TestCase


@dataclass
class TestResult:
    test_id: str
    description: str
    passed: bool
    reason: str


@dataclass
class JudgeResult:
    passed: bool
    test_results: List[TestResult]
    score: int  # 0-100
    feedback: str


def run_static_tests(code: str, scenario: Scenario) -> List[TestResult]:
    results = []
    for tc in scenario.test_cases:
        if tc.type == "code_contains":
            found = tc.required in code if tc.required else True
            passed = found if tc.expect == "pass" else not found
            reason = (
                f'"{tc.required}" がコードに含まれています' if found
                else f'"{tc.required}" がコードに含まれていません'
            )
        elif tc.type == "code_not_contains":
            found = tc.forbidden in code if tc.forbidden else False
            passed = not found if tc.expect == "blocked" else found
            reason = (
                f'問題のパターン "{tc.forbidden}" が残っています' if found
                else f'問題のパターンは除去されています'
            )
        else:
            passed = False
            reason = f"未知のテスト種別: {tc.type}"

        results.append(TestResult(
            test_id=tc.id,
            description=tc.description,
            passed=passed,
            reason=reason,
        ))
    return results


def judge(code: str, scenario: Scenario) -> JudgeResult:
    test_results = run_static_tests(code, scenario)
    passed_count = sum(1 for r in test_results if r.passed)
    total = len(test_results)
    all_passed = passed_count == total
    score = round((passed_count / total) * 100) if total > 0 else 0

    if all_passed:
        feedback = "すべてのテストを通過しました。脆弱性が正しく修正されています。"
    elif passed_count == 0:
        feedback = "テストがすべて失敗しています。コードの修正方針を見直してください。"
    else:
        failed = [r for r in test_results if not r.passed]
        feedback = f"{passed_count}/{total} テスト通過。未解決の問題: " + " / ".join(r.description for r in failed)

    return JudgeResult(
        passed=all_passed,
        test_results=test_results,
        score=score,
        feedback=feedback,
    )
