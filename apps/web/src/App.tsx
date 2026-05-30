import { useEffect, useMemo, useState } from 'react'

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

const WINNER_LABELS: Record<string, string> = {
  player: '✅ あなたの勝利',
  ai: '❌ AI の勝利',
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

export default function App() {
  const [game, setGame] = useState<GameState | null>(null)
  const [events, setEvents] = useState<EventItem[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const finished = useMemo(() => game?.status === 'finished', [game])
  const lastAttack = useMemo(() => {
    const e = [...events].reverse().find(ev => ev.event_type === 'attack_chosen')
    return e ? String(e.payload.attack ?? '') : null
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

  return (
    <div className="app">
      <header className="header">
        <div>
          <p className="eyebrow">Security Simulation MVP</p>
          <h1>AI攻撃 vs ユーザー防御</h1>
        </div>
        <button onClick={startGame} disabled={busy} className="secondary">
          新しいゲーム
        </button>
      </header>

      {error && <div className="card error">{error}</div>}

      <section className="grid">
        <div className="card">
          <h2>ステータス <span className="turn-badge">Turn {game?.turn_number ?? '-'} / {game?.max_turns ?? '-'}</span></h2>
          <StatBar label="耐久" value={game?.state.integrity ?? 100} />
          <StatBar label="防御力" value={game?.state.posture ?? 100} />
          <StatBar label="警戒値" value={game?.state.alert ?? 0} danger />
          {lastAttack && !finished && (
            <p className="last-attack">前回のAI攻撃: <strong>{ATTACK_LABELS[lastAttack] ?? lastAttack}</strong></p>
          )}
        </div>

        <div className="card">
          <h2>防御選択</h2>
          <div className="actions">
            {DEFENSES.map((d) => (
              <button key={d.key} onClick={() => defend(d.key)} disabled={busy || finished} className="defense-btn">
                <span className="btn-label">{d.label}</span>
                <span className="btn-desc">{d.desc}</span>
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="card log-card">
        <h2>イベントログ</h2>
        <div className="log">
          {events.length === 0 && <p className="log-empty">イベントなし</p>}
          {[...events].reverse().map((e) => (
            <div key={e.id} className={`log-row log-${e.actor}`}>
              <div className="log-top">
                <span className="log-seq">#{e.seq}</span>
                <span className={`log-type log-type-${e.event_type}`}>{e.event_type}</span>
                <span className="log-actor">{e.actor}</span>
                <span className="log-time">{new Date(e.created_at).toLocaleTimeString()}</span>
              </div>
              <pre className="log-payload">{JSON.stringify(e.payload, null, 2)}</pre>
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
