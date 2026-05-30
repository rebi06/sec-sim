import { useEffect, useMemo, useState } from 'react'
import ScenarioGame from './ScenarioGame'

type GameState = {
  id: string
  status: string
  ruleset_version: string
  turn_number: number
  max_turns: number
  state: {
    integrity: number
    posture: number
    alert: number
    winner: string
    status_flags: Record<string, unknown>
  }
}

type EventItem = {
  id: string
  seq: number
  event_type: string
  actor: string
  payload: Record<string, unknown>
  correlation_id: string | null
  created_at: string
}

type TurnResult = {
  attack: string
  defense: string
  delta_integrity: number
  delta_posture: number
  delta_alert: number
  notes: string[]
}

const DEFENSES = [
  { key: 'fortify', label: '強化', desc: 'posture+12 / 攻撃35%軽減' },
  { key: 'monitor', label: '監視', desc: 'alert-8 / 攻撃55%軽減' },
  { key: 'recover', label: '復旧', desc: 'integrity+10 / alert-10' },
] as const

const ATTACK_LABELS: Record<string, string> = {
  recon_pressure: '偵察圧力',
  resource_drain: 'リソース枯渇',
  confusion: '攪乱',
}

const DEFENSE_LABELS: Record<string, string> = {
  fortify: '強化',
  monitor: '監視',
  recover: '復旧',
}

const WINNER_LABELS: Record<string, string> = {
  player: '✅ あなたの勝利',
  ai: '❌ AI の勝利',
}

function delta(n: number, invert = false) {
  const positive = invert ? n < 0 : n > 0
  const sign = n > 0 ? '+' : ''
  return <span className={positive ? 'delta-good' : n < 0 ? 'delta-bad' : 'delta-zero'}>{sign}{n}</span>
}

function StatBar({ label, value, max = 100, danger }: { label: string; value: number; max?: number; danger?: boolean }) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100))
  const color = danger
    ? pct >= 70 ? 'bar-danger' : pct >= 40 ? 'bar-warn' : 'bar-ok'
    : pct <= 30 ? 'bar-danger' : pct <= 60 ? 'bar-warn' : 'bar-ok'
  return (
    <div className="stat-row">
      <span className="stat-label">{label}</span>
      <div className="bar-track">
        <div className={`bar-fill ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="stat-value">{value}</span>
    </div>
  )
}

type Mode = 'status' | 'scenario'

export default function App() {
  const [mode, setMode] = useState<Mode>('scenario')
  const [game, setGame] = useState<GameState | null>(null)
  const [events, setEvents] = useState<EventItem[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const finished = useMemo(() => game?.status === 'finished', [game])

  const lastResult = useMemo<TurnResult | null>(() => {
    const e = [...events].reverse().find(ev => ev.event_type === 'resolution_applied')
    if (!e) return null
    const p = e.payload
    return {
      attack: String(p.attack ?? ''),
      defense: String(p.defense ?? ''),
      delta_integrity: Number(p.delta_integrity ?? 0),
      delta_posture: Number(p.delta_posture ?? 0),
      delta_alert: Number(p.delta_alert ?? 0),
      notes: Array.isArray(p.notes) ? p.notes.map(String) : [],
    }
  }, [events])

  async function startGame() {
    setBusy(true)
    setError(null)
    setEvents([])
    try {
      const res = await fetch('/api/games', { method: 'POST' })
      const data = (await res.json()) as GameState
      setGame(data)
      await refreshEvents(data.id)
    } catch {
      setError('ゲーム開始に失敗しました')
    } finally {
      setBusy(false)
    }
  }

  async function refreshEvents(gameId: string) {
    const res = await fetch(`/api/games/${gameId}/events`)
    const data = (await res.json()) as EventItem[]
    setEvents(data)
  }

  async function defend(defense: string) {
    if (!game || busy || finished) return
    setBusy(true)
    setError(null)
    try {
      const res = await fetch(`/api/games/${game.id}/actions/defend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ defense }),
      })
      const data = (await res.json()) as GameState
      setGame(data)
      await refreshEvents(game.id)
    } catch {
      setError('ターン進行に失敗しました')
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => { void startGame() }, [])

  if (mode === 'scenario') {
    return (
      <div className="app app-scenario">
        <header className="header">
          <div>
            <p className="eyebrow">Security Simulation MVP</p>
            <h1>脆弱性修正チャレンジ</h1>
          </div>
          <button onClick={() => setMode('status')} className="secondary">
            ステータスゲームへ
          </button>
        </header>
        <ScenarioGame scenarioId="sqli-login-001" />
      </div>
    )
  }

  return (
    <div className="app">
      <header className="header">
        <div>
          <p className="eyebrow">Security Simulation MVP</p>
          <h1>AI攻撃 vs ユーザー防御</h1>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={() => setMode('scenario')} className="secondary">
            シナリオゲームへ
          </button>
          <button onClick={startGame} disabled={busy} className="secondary">
            新しいゲーム
          </button>
        </div>
      </header>

      {error && <div className="card error">{error}</div>}

      <section className="grid">
        {/* ステータス */}
        <div className="card">
          <h2>ステータス <span className="turn-badge">Turn {game?.turn_number ?? '-'} / {game?.max_turns ?? '-'}</span></h2>
          <StatBar label="耐久" value={game?.state.integrity ?? 100} />
          <StatBar label="防御力" value={game?.state.posture ?? 100} />
          <StatBar label="警戒値" value={game?.state.alert ?? 0} danger />

          {lastResult && !finished && (
            <div className="turn-result">
              <div className="turn-result-header">
                <span className="tr-label">AI攻撃</span>
                <span className="tr-attack">{ATTACK_LABELS[lastResult.attack] ?? lastResult.attack}</span>
                <span className="tr-label">あなたの選択</span>
                <span className="tr-defense">{DEFENSE_LABELS[lastResult.defense] ?? lastResult.defense}</span>
              </div>
              <div className="turn-result-deltas">
                <div className="td-item">
                  <span>耐久</span>
                  {delta(lastResult.delta_integrity)}
                </div>
                <div className="td-item">
                  <span>防御力</span>
                  {delta(lastResult.delta_posture)}
                </div>
                <div className="td-item">
                  <span>警戒値</span>
                  {delta(lastResult.delta_alert, true)}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 防御選択 */}
        <div className="card">
          <h2>防御選択</h2>
          <div className="defense-hint">毎ターン1つ選んでください。AIの攻撃を受けた後に効果が適用されます。</div>
          <div className="actions">
            {DEFENSES.map((d) => (
              <button key={d.key} onClick={() => defend(d.key)} disabled={busy || finished} className="defense-btn">
                <span className="btn-label">{d.label}</span>
                <span className="btn-desc">{d.desc}</span>
              </button>
            ))}
          </div>
          <div className="defense-guide">
            <div className="dg-row"><strong>強化</strong> — 防御力を積み上げる。防御力が低いとき優先。</div>
            <div className="dg-row"><strong>監視</strong> — 攻撃の影響を最も抑える。警戒値が上がりそうなとき有効。</div>
            <div className="dg-row"><strong>復旧</strong> — 耐久を回復。耐久が低いとき優先。</div>
          </div>
        </div>
      </section>

      {/* イベントログ */}
      <section className="card log-card">
        <h2>イベントログ</h2>
        <div className="log">
          {events.length === 0 && <p className="log-empty">イベントなし</p>}
          {[...events].reverse().map((e) => (
            <div key={e.id} className={`log-row log-${e.actor}`}>
              <div className="log-top">
                <span className="log-seq">#{e.seq}</span>
                <span className={`log-type`}>{e.event_type}</span>
                <span className="log-actor">{e.actor}</span>
                <span className="log-time">{new Date(e.created_at).toLocaleTimeString()}</span>
              </div>
              {e.event_type === 'resolution_applied' ? (
                <div className="log-resolution">
                  <span>攻撃: <strong>{ATTACK_LABELS[String(e.payload.attack)] ?? String(e.payload.attack)}</strong></span>
                  <span>防御: <strong>{DEFENSE_LABELS[String(e.payload.defense)] ?? String(e.payload.defense)}</strong></span>
                  <span>耐久 {delta(Number(e.payload.delta_integrity))}</span>
                  <span>防御力 {delta(Number(e.payload.delta_posture))}</span>
                  <span>警戒値 {delta(Number(e.payload.delta_alert), true)}</span>
                </div>
              ) : (
                <pre className="log-payload">{JSON.stringify(e.payload, null, 2)}</pre>
              )}
            </div>
          ))}
        </div>
      </section>

      {finished && game && (
        <div className="overlay" onClick={startGame}>
          <div className="overlay-box">
            <p className="overlay-result">{WINNER_LABELS[game.state.winner] ?? game.state.winner}</p>
            <p className="overlay-sub">Turn {game.turn_number - 1} / {game.max_turns} 完了</p>
            <p className="overlay-hint">クリックして新しいゲームを開始</p>
          </div>
        </div>
      )}
    </div>
  )
}
