import Editor from '@monaco-editor/react'
import { useEffect, useState } from 'react'

type Hint = { level1: string; level2: string; level3: string }

type Scenario = {
  id: string
  title: string
  category: string
  difficulty: string
  service_name: string
  description: string
  vulnerable_code: string
  hint: Hint
}

type TestResult = {
  test_id: string
  description: string
  passed: boolean
  reason: string
}

type SubmitResult = {
  passed: boolean
  score: number
  feedback: string
  test_results: TestResult[]
  explanation: string | null
}

const DIFFICULTY_LABEL: Record<string, string> = {
  easy: 'Easy',
  normal: 'Normal',
  hard: 'Hard',
}

const DIFFICULTY_COLOR: Record<string, string> = {
  easy: 'diff-easy',
  normal: 'diff-normal',
  hard: 'diff-hard',
}

export default function ScenarioGame({ scenarioId }: { scenarioId: string }) {
  const [scenario, setScenario] = useState<Scenario | null>(null)
  const [code, setCode] = useState('')
  const [submitResult, setSubmitResult] = useState<SubmitResult | null>(null)
  const [hintLevel, setHintLevel] = useState(0)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`/api/scenarios/${scenarioId}`)
      .then(r => r.json())
      .then((s: Scenario) => {
        setScenario(s)
        setCode(s.vulnerable_code)
        setSubmitResult(null)
        setHintLevel(0)
      })
      .catch(() => setError('シナリオの読み込みに失敗しました'))
  }, [scenarioId])

  async function handleSubmit() {
    if (!scenario || busy) return
    setBusy(true)
    setError(null)
    try {
      const res = await fetch(`/api/scenarios/${scenarioId}/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, hint_used: hintLevel }),
      })
      setSubmitResult(await res.json())
    } catch {
      setError('提出に失敗しました')
    } finally {
      setBusy(false)
    }
  }

  function handleReset() {
    if (!scenario) return
    setCode(scenario.vulnerable_code)
    setSubmitResult(null)
    setHintLevel(0)
  }

  function showHint() {
    setHintLevel(h => Math.min(h + 1, 3))
  }

  const currentHint = scenario
    ? hintLevel === 1 ? scenario.hint.level1
    : hintLevel === 2 ? scenario.hint.level2
    : hintLevel === 3 ? scenario.hint.level3
    : null
    : null

  if (!scenario) return <div className="scenario-loading">読み込み中...</div>

  return (
    <div className="scenario-layout">
      {/* 左ペイン: 情報 */}
      <div className="scenario-info">
        <div className="scenario-meta">
          <span className={`difficulty-badge ${DIFFICULTY_COLOR[scenario.difficulty]}`}>
            {DIFFICULTY_LABEL[scenario.difficulty]}
          </span>
          <span className="category-badge">{scenario.category}</span>
        </div>
        <h2 className="scenario-title">{scenario.title}</h2>
        <p className="service-name">対象: {scenario.service_name}</p>
        <p className="scenario-desc">{scenario.description}</p>

        <div className="scenario-actions">
          <button onClick={handleSubmit} disabled={busy || submitResult?.passed} className="submit-btn">
            {busy ? '判定中...' : '提出する'}
          </button>
          <button onClick={handleReset} className="secondary reset-btn">リセット</button>
          {hintLevel < 3 && !submitResult?.passed && (
            <button onClick={showHint} className="hint-btn">
              ヒント {hintLevel > 0 ? `(${hintLevel}/3)` : ''}
            </button>
          )}
        </div>

        {currentHint && (
          <div className="hint-box">
            <span className="hint-label">ヒント {hintLevel}/3</span>
            <p>{currentHint}</p>
          </div>
        )}

        {error && <div className="scenario-error">{error}</div>}

        {submitResult && (
          <div className={`result-box ${submitResult.passed ? 'result-pass' : 'result-fail'}`}>
            <div className="result-header">
              <span>{submitResult.passed ? '✅ クリア！' : '❌ 未解決'}</span>
              <span className="result-score">スコア {submitResult.score}/100</span>
            </div>
            <p className="result-feedback">{submitResult.feedback}</p>

            <div className="test-results">
              {submitResult.test_results.map(tr => (
                <div key={tr.test_id} className={`tr-row ${tr.passed ? 'tr-pass' : 'tr-fail'}`}>
                  <span>{tr.passed ? '✓' : '✗'}</span>
                  <span>{tr.description}</span>
                  <span className="tr-reason">{tr.reason}</span>
                </div>
              ))}
            </div>

            {submitResult.explanation && (
              <div className="explanation">
                <h4>解説</h4>
                <pre>{submitResult.explanation}</pre>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 右ペイン: コードエディタ */}
      <div className="editor-pane">
        <div className="editor-header">
          <span>login.py</span>
          <span className="editor-hint-text">脆弱性を修正してください</span>
        </div>
        <Editor
          height="100%"
          defaultLanguage="python"
          value={code}
          onChange={v => setCode(v ?? '')}
          theme="vs-dark"
          options={{
            fontSize: 14,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            lineNumbers: 'on',
            readOnly: submitResult?.passed ?? false,
          }}
        />
      </div>
    </div>
  )
}
