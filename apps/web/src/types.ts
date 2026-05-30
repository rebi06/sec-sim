export type ScenarioSummary = {
  id: string
  title: string
  category: string
  difficulty: string
  service_name: string
}

export type GameMode =
  | { type: 'lobby' }
  | { type: 'list'; filters: { difficulty: string; category: string } }
  | { type: 'play'; scenarioId: string; returnTo: 'list' | 'random' }
  | { type: 'random'; difficulty: string; streak: number; cleared: string[] }
