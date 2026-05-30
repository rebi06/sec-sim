from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List

from openai import OpenAI

from app.domain.scenario import Scenario


@dataclass
class AttackResult:
    payload: str
    blocked: bool
    reason: str


@dataclass
class SimulationResult:
    attacks: List[AttackResult]
    all_blocked: bool
    summary: str


_PAYLOADS: dict[str, List[str]] = {
    "SQL Injection": [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "' UNION SELECT * FROM users --",
        "admin'--",
        "' OR 1=1 --",
    ],
    "XSS": [
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        "<b onmouseover=alert(1)>hover</b>",
        "javascript:alert(1)",
        "<svg/onload=alert(1)>",
    ],
    "Path Traversal": [
        "../etc/passwd",
        "../../secret.txt",
        "..%2F..%2Fetc%2Fpasswd",
        "....//....//etc/passwd",
        "../../../root/.ssh/id_rsa",
    ],
    "IDOR": [
        "他ユーザーのID=102を直接指定",
        "連番推測: ID=1, 2, 3 ...",
        "別ユーザーのリソースID=999",
        "予測可能なID=user-b|101",
        "権限外リソース: admin_id=1",
    ],
}

_PROMPT_TEMPLATE = """\
あなたはセキュリティ研究者です。以下のコードに対して、攻撃ペイロードが「突破できるか / ブロックされるか」を判定してください。

## 対象コード
```
{code}
```

## 脆弱性カテゴリ
{category}

## 攻撃ペイロード
{payload}

## 指示
上記のペイロードをこのコードに対して使った場合、攻撃が成立するか判定してください。
以下のJSON形式のみで回答してください（他のテキスト不要）：

{{"blocked": true または false, "reason": "日本語で1文の理由"}}

- blocked: true → コードが攻撃を防げている
- blocked: false → コードが攻撃を防げていない（脆弱）
"""


def simulate_attacks(code: str, scenario: Scenario) -> SimulationResult:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    payloads = _PAYLOADS.get(scenario.category, _PAYLOADS["SQL Injection"])

    results: List[AttackResult] = []
    for payload in payloads:
        prompt = _PROMPT_TEMPLATE.format(
            code=code,
            category=scenario.category,
            payload=payload,
        )
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=120,
            )
            import json
            text = response.choices[0].message.content.strip()
            data = json.loads(text)
            blocked = bool(data.get("blocked", False))
            reason = str(data.get("reason", ""))
        except Exception as e:
            blocked = False
            reason = f"判定エラー: {e}"

        results.append(AttackResult(payload=payload, blocked=blocked, reason=reason))

    all_blocked = all(r.blocked for r in results)
    blocked_count = sum(1 for r in results if r.blocked)
    summary = (
        f"全 {len(results)} 件の攻撃をブロックしました。コードは安全です。"
        if all_blocked
        else f"{len(results)} 件中 {blocked_count} 件ブロック。{len(results) - blocked_count} 件の攻撃が突破しています。"
    )

    return SimulationResult(attacks=results, all_blocked=all_blocked, summary=summary)
