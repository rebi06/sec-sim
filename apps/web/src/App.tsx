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
  created_at: string
}

const DEFENSES = [
  { key: 'fortify', label: '強化' },
  { key: 'monitor', label: '監視' },
  { key: 'recover', label: '復旧' },
] as const

export default function App() {
  const [game, setGame] = useState<GameState | null>(null)
  const [events, setEvents] = useState<EventItem[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const finished = useMemo(() => game?.status === 'finished', [game])

  async function startGame() {
    setBusy(true)
    setError(null)
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

  useEffect(() => {
    void startGame()
  }, [])

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
          <h2>ステータス</h2>
          <div className="stats">
            <div><span>耐久</span><strong>{game?.state.integrity ?? '-'}</strong></div>
            <div><span>防御力</span><strong>{game?.state.posture ?? '-'}</strong></div>
            <div><span>警戒値</span><strong>{game?.state.alert ?? '-'}</strong></div>
            <div><span>ターン</span><strong>{game?.turn_number ?? '-'}/{game?.max_turns ?? '-'}</strong></div>
          </div>
          {game?.status === 'finished' && (
            <div className="result">結果: {game.state.winner}</div>
          )}
        </div>

        <div className="card">
          <h2>防御選択</h2>
          <div className="actions">
            {DEFENSES.map((d) => (
              <button key={d.key} onClick={() => defend(d.key)} disabled={busy || finished}>
                {d.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="card log-card">
        <h2>イベントログ</h2>
        <div className="log">
          {events.map((e) => (
            <div key={e.id} className="log-row">
              <div className="log-top">
                <span>#{e.seq}</span>
                <span>{e.event_type}</span>
                <span>{e.actor}</span>
                <span>{new Date(e.created_at).toLocaleTimeString()}</span>
              </div>
              <pre>{JSON.stringify(e.payload, null, 2)}</pre>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
