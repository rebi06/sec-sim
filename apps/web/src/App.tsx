import { useCallback, useEffect, useMemo, useState } from 'react'
import Lobby from './Lobby'
import ScenarioGame from './ScenarioGame'
import ScenarioList from './ScenarioList'
import type { GameMode, ScenarioSummary } from './types'

// ──────────────────────────────────────────────
// Status game helpers (existing turn-based game)
// ──────────────────────────────────────────────

type GameState = {
  id: string
  status: string
  ruleset_version: string
  turn_number: number
  max_turns: number
  state: { integrity: number; posture: number; alert: number; winner: string; status_flags: Record<string, unknown> }
}
type EventItem = {
  id: string; seq: number; event_type: string; actor: string
  payload: Record<string, unknown>; correlation_id: string | null; created_at: string
}
type TurnResult = { attack: string; defense: string; delta_integrity: number; delta_posture: number; delta_alert: number; notes: string[] }

const DEFENSES = [
  { key: 'fortify', label: '強化', desc: 'posture+12 / 攻撃35%軽減' },
  { key: 'monitor', label: '監視', desc: 'alert-8 / 攻撃55%軽減' },
  { key: 'recover', label: '復旧', desc: 'integrity+10 / alert-10' },
] as const
const ATTACK_LABELS: Record<string, string> = { recon_pressure: '偵察圧力', resource_drain: 'リソース枯渇', confusion: '攪乱' }
const DEFENSE_LABELS: Record<string, string> = { fortify: '強化', monitor: '監視', recover: '復旧' }
const WINNER_LABELS: Record<string, string> = { player: '✅ あなたの勝利', ai: '❌ AI の勝利' }

function delta(n: number, invert = false) {
  const positive = invert ? n < 0 : n > 0
  const sign = n > 0 ? '+' : ''
  return <span className={positive ? 'delta-good' : n < 0 ? 'delta-bad' : 'delta-zero'}>{sign}{n}</span>
}

function StatBar({ label, value, danger }: { label: string; value: number; danger?: boolean }) {
  const pct = Math.max(0, Math.min(100, value))
  const color = danger
    ? pct >= 70 ? 'bar-danger' : pct >= 40 ? 'bar-warn' : 'bar-ok'
    : pct <= 30 ? 'bar-danger' : pct <= 60 ? 'bar-warn' : 'bar-ok'
  return (
    <div className="stat-row">
      <span className="stat-label">{label}</span>
      <div className="bar-track"><div className={`bar-fill ${color}`} style={{ width: `${pct}%` }} /></div>
      <span className="stat-value">{value}</span>
    </div>
  )
}

// ──────────────────────────────────────────────
// Random mode controller
// ──────────────────────────────────────────────

function useRandomMode(difficulty: string, clearedIds: string[]) {
  const [pool, setPool] = useState<ScenarioSummary[]>([])
  const [current, setCurrent] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/scenarios')
      .then(r => r.json())
      .then((list: ScenarioSummary[]) => {
        setPool(list.filter(s => s.difficulty === difficulty))
      })
  }, [difficulty])

  const remaining = useMemo(
    () => pool.filter(s => !clearedIds.includes(s.id)),
    [pool, clearedIds],
  )

  useEffect(() => {
    if (pool.length === 0) return
    if (current && !clearedIds.includes(current)) return
    if (remaining.length === 0) { setCurrent(null); return }
    const next = remaining[Math.floor(Math.random() * remaining.length)]
    setCurrent(next.id)
  }, [pool, clearedIds, remaining])

  return { current, totalCount: pool.length, remainingCount: remaining.length }
}

// ──────────────────────────────────────────────
// Root router
// ──────────────────────────────────────────────

export default function App() {
  const [mode, setMode] = useState<GameMode>({ type: 'lobby' })

  const navigate = useCallback((m: GameMode) => setMode(m), [])

  // ---- scenario list mode ----
  if (mode.type === 'list') {
    return <ScenarioList initialFilters={mode.filters} onNavigate={navigate} />
  }

  // ---- scenario play from list ----
  if (mode.type === 'play') {
    return (
      <div className="app app-scenario">
        <ScenarioGame
          scenarioId={mode.scenarioId}
          onNavigate={navigate}
          onClear={() => navigate({ type: 'list', filters: { difficulty: '', category: '' } })}
        />
      </div>
    )
  }

  // ---- random mode ----
  if (mode.type === 'random') {
    return <RandomMode mode={mode} onNavigate={navigate} />
  }

  // ---- lobby ----
  return (
    <div className="app">
      <Lobby onNavigate={navigate} />
    </div>
  )
}

// ──────────────────────────────────────────────
// Random mode wrapper (needs hooks so it's a component)
// ──────────────────────────────────────────────

function RandomMode({ mode, onNavigate }: { mode: Extract<GameMode, { type: 'random' }>; onNavigate: (m: GameMode) => void }) {
  const { current, totalCount, remainingCount } = useRandomMode(mode.difficulty, mode.cleared)

  function handleClear() {
    if (!current) return
    onNavigate({
      type: 'random',
      difficulty: mode.difficulty,
      streak: mode.streak + 1,
      cleared: [...mode.cleared, current],
    })
  }

  // 全クリ
  if (current === null && totalCount > 0) {
    return (
      <div className="app">
        <div className="allclear">
          <p className="allclear-icon">🎉</p>
          <h2>全問クリア！</h2>
          <p className="allclear-streak">最終連続クリア数: {mode.streak}</p>
          <div className="allclear-actions">
            <button className="submit-btn" onClick={() => onNavigate({ type: 'random', difficulty: mode.difficulty, streak: 0, cleared: [] })}>
              もう一周する
            </button>
            <button className="secondary" onClick={() => onNavigate({ type: 'lobby' })}>
              ロビーへ戻る
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!current) return <div className="app"><div className="scenario-loading">読み込み中...</div></div>

  return (
    <div className="app app-scenario">
      <div className="random-progress">
        <button className="back-btn" onClick={() => onNavigate({ type: 'lobby' })}>← ロビー</button>
        <span className="random-label">ランダムモード</span>
        <span className="random-count">残り {remainingCount} / {totalCount} 問</span>
        {mode.streak > 0 && <span className="streak-badge">🔥 {mode.streak} 連続クリア</span>}
      </div>
      <ScenarioGame
        scenarioId={current}
        streak={mode.streak}
        onNavigate={onNavigate}
        onClear={handleClear}
      />
    </div>
  )
}
