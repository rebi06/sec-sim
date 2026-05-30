import { useEffect, useState } from 'react'
import type { GameMode, ScenarioSummary } from './types'

const DIFFICULTY_ORDER = ['easy', 'normal', 'hard']
const DIFFICULTY_LABEL: Record<string, string> = { easy: 'Easy', normal: 'Normal', hard: 'Hard' }
const DIFFICULTY_COLOR: Record<string, string> = { easy: 'diff-easy', normal: 'diff-normal', hard: 'diff-hard' }

export default function ScenarioList({
  initialFilters,
  onNavigate,
}: {
  initialFilters: { difficulty: string; category: string }
  onNavigate: (mode: GameMode) => void
}) {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([])
  const [difficulty, setDifficulty] = useState(initialFilters.difficulty)
  const [category, setCategory] = useState(initialFilters.category)

  useEffect(() => {
    fetch('/api/scenarios')
      .then(r => r.json())
      .then(setScenarios)
      .catch(() => {})
  }, [])

  const categories = [...new Set(scenarios.map(s => s.category))].sort()
  const difficulties = DIFFICULTY_ORDER.filter(d => scenarios.some(s => s.difficulty === d))

  const filtered = scenarios.filter(s => {
    if (difficulty && s.difficulty !== difficulty) return false
    if (category && s.category !== category) return false
    return true
  })

  return (
    <div className="scene-list-page">
      <div className="scene-list-header">
        <button className="back-btn" onClick={() => onNavigate({ type: 'lobby' })}>← 戻る</button>
        <h2>問題一覧</h2>
      </div>

      {/* フィルター */}
      <div className="filters">
        <div className="filter-group">
          <span className="filter-label">難易度</span>
          <div className="filter-pills">
            <button
              className={`pill ${difficulty === '' ? 'pill-active' : ''}`}
              onClick={() => setDifficulty('')}
            >すべて</button>
            {difficulties.map(d => (
              <button
                key={d}
                className={`pill ${difficulty === d ? 'pill-active' : ''}`}
                onClick={() => setDifficulty(d)}
              >{DIFFICULTY_LABEL[d]}</button>
            ))}
          </div>
        </div>
        <div className="filter-group">
          <span className="filter-label">カテゴリ</span>
          <div className="filter-pills">
            <button
              className={`pill ${category === '' ? 'pill-active' : ''}`}
              onClick={() => setCategory('')}
            >すべて</button>
            {categories.map(c => (
              <button
                key={c}
                className={`pill ${category === c ? 'pill-active' : ''}`}
                onClick={() => setCategory(c)}
              >{c}</button>
            ))}
          </div>
        </div>
      </div>

      {/* 問題リスト */}
      <div className="scenario-cards">
        {filtered.length === 0 && (
          <p className="no-results">該当する問題がありません</p>
        )}
        {filtered.map(s => (
          <button
            key={s.id}
            className="scenario-card"
            onClick={() => onNavigate({ type: 'play', scenarioId: s.id, returnTo: 'list' })}
          >
            <div className="sc-meta">
              <span className={`difficulty-badge ${DIFFICULTY_COLOR[s.difficulty]}`}>
                {DIFFICULTY_LABEL[s.difficulty]}
              </span>
              <span className="category-badge">{s.category}</span>
            </div>
            <div className="sc-title">{s.title}</div>
            <div className="sc-service">{s.service_name}</div>
          </button>
        ))}
      </div>
    </div>
  )
}
