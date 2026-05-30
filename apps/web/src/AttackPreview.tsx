import { useState } from 'react'

type AttackResult = {
  payload: string
  blocked: boolean
  reason: string
}

type SimulateResponse = {
  attacks: AttackResult[]
  all_blocked: boolean
  summary: string
}

export default function AttackPreview({
  scenarioId,
  code,
  disabled,
}: {
  scenarioId: string
  code: string
  disabled: boolean
}) {
  const [result, setResult] = useState<SimulateResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [revealed, setRevealed] = useState<number[]>([])

  async function runSimulation() {
    setLoading(true)
    setError(null)
    setResult(null)
    setRevealed([])
    try {
      const res = await fetch(`/api/scenarios/${scenarioId}/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      })
      const data: SimulateResponse = await res.json()
      setResult(data)
      // 攻撃結果を1件ずつ順番に表示するアニメーション
      data.attacks.forEach((_, i) => {
        setTimeout(() => setRevealed(prev => [...prev, i]), i * 600)
      })
    } catch {
      setError('シミュレーションに失敗しました')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="attack-preview">
      <div className="ap-header">
        <div>
          <h3 className="ap-title">⚔️ AI攻撃シミュレーション</h3>
          <p className="ap-desc">現在のコードに対してAIが攻撃を試みます</p>
        </div>
        <button
          className="ap-btn"
          onClick={runSimulation}
          disabled={loading || disabled}
        >
          {loading ? (
            <span className="ap-loading">攻撃中<span className="dots">...</span></span>
          ) : '攻撃を試みる'}
        </button>
      </div>

      {error && <div className="ap-error">{error}</div>}

      {loading && (
        <div className="ap-scanning">
          <div className="scan-line" />
          <p>AIが攻撃パターンを分析しています...</p>
        </div>
      )}

      {result && (
        <div className="ap-results">
          <div className={`ap-summary ${result.all_blocked ? 'summary-safe' : 'summary-danger'}`}>
            <span>{result.all_blocked ? '🛡️' : '💥'}</span>
            <span>{result.summary}</span>
          </div>

          <div className="ap-attacks">
            {result.attacks.map((attack, i) => (
              revealed.includes(i) ? (
                <div
                  key={i}
                  className={`ap-attack ${attack.blocked ? 'attack-blocked' : 'attack-breached'}`}
                >
                  <div className="attack-top">
                    <span className="attack-icon">{attack.blocked ? '🛡️ ブロック' : '💥 突破'}</span>
                    <code className="attack-payload">{attack.payload}</code>
                  </div>
                  <p className="attack-reason">{attack.reason}</p>
                </div>
              ) : (
                <div key={i} className="ap-attack attack-pending">
                  <span className="pending-dot" />
                  <span className="pending-dot" />
                  <span className="pending-dot" />
                </div>
              )
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
