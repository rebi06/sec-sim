import { useEffect, useState } from 'react'
import type { GameMode, ScenarioSummary } from './types'

const DIFFICULTY_ORDER = ['easy', 'normal', 'hard']
const DIFFICULTY_LABEL: Record<string, string> = { easy: 'Easy', normal: 'Normal', hard: 'Hard' }
const DIFFICULTY_COLOR: Record<string, string> = { easy: 'diff-easy', normal: 'diff-normal', hard: 'diff-hard' }

export default function Lobby({ onNavigate }: { onNavigate: (mode: GameMode) => void }) {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([])

  useEffect(() => {
    fetch('/api/scenarios')
      .then(r => r.json())
      .then(setScenarios)
      .catch(() => {})
  }, [])

  const categories = [...new Set(scenarios.map(s => s.category))].sort()
  const difficulties = DIFFICULTY_ORDER.filter(d => scenarios.some(s => s.difficulty === d))

  const countByDifficulty = (d: string) => scenarios.filter(s => s.difficulty === d).length

  return (
    <div className="lobby">
      <div className="lobby-hero">
        <p className="eyebrow">Security Simulation MVP</p>
        <h1>脆弱性修正チャレンジ</h1>
        <p className="lobby-sub">AIが攻撃を仕掛けているWebアプリの脆弱性を発見・修正して守れ</p>
      </div>

      <div className="lobby-grid">
        {/* 問題を選ぶ */}
        <div className="lobby-card">
          <div className="lobby-card-icon">📚</div>
          <h2>問題を選ぶ</h2>
          <p>カテゴリと難易度でフィルターして好きな問題を選択</p>
          <div className="lobby-tags">
            {categories.map(c => (
              <span key={c} className="tag">{c}</span>
            ))}
          </div>
          <button
            className="lobby-btn"
            onClick={() => onNavigate({ type: 'list', filters: { difficulty: '', category: '' } })}
          >
            問題一覧へ →
          </button>
        </div>

        {/* ランダムモード */}
        <div className="lobby-card">
          <div className="lobby-card-icon">🎲</div>
          <h2>ランダムモード</h2>
          <p>難易度を選んでスタート。クリアするたびに次の問題がランダムに出題される</p>
          <div className="lobby-difficulty-row">
            {difficulties.map(d => (
              <button
                key={d}
                className={`difficulty-select-btn ${DIFFICULTY_COLOR[d]}`}
                onClick={() => onNavigate({ type: 'random', difficulty: d, streak: 0, cleared: [] })}
              >
                <span className="dsb-label">{DIFFICULTY_LABEL[d]}</span>
                <span className="dsb-count">{countByDifficulty(d)}問</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 問題数サマリー */}
      {scenarios.length > 0 && (
        <div className="lobby-stats">
          <span>全 {scenarios.length} 問</span>
          {difficulties.map(d => (
            <span key={d}>
              <span className={`difficulty-badge ${DIFFICULTY_COLOR[d]}`}>{DIFFICULTY_LABEL[d]}</span>
              {countByDifficulty(d)}問
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
