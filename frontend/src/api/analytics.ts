const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export interface TypeDistribution {
  type: string
  count: number
}

export interface GenerationStats {
  generation: number
  hp: number
  attack: number
  defense: number
  sp_attack: number
  sp_defense: number
  speed: number
}

export interface ScatterPoint {
  name: string
  speed: number
  power_score: number
  primary_type: string | null
}

export interface TypeChartData {
  generation: number
  types: string[]
  matrix: Record<string, Record<string, number>>
}

export const fetchTypeDistribution = (): Promise<TypeDistribution[]> =>
  fetch(`${API}/analytics/types`).then((r) => r.json())

export const fetchGenerationStats = (): Promise<GenerationStats[]> =>
  fetch(`${API}/analytics/generations`).then((r) => r.json())

export const fetchScatterData = (): Promise<ScatterPoint[]> =>
  fetch(`${API}/analytics/scatter`).then((r) => r.json())

export const fetchTypeChart = (generation = 9): Promise<TypeChartData> =>
  fetch(`${API}/analytics/type-chart?generation=${generation}`).then((r) =>
    r.json()
  )
