const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export interface TeamMember {
  id: number
  name_fr: string | null
  name_en: string
  sprite_url: string | null
  generation: number
  types: string[]
  weaknesses: string[]
  resistances: string[]
}

export interface Weakness {
  type: string
  weak_count: number
  members: number[]
}

export interface OffensiveCoverage {
  covered: string[]
  gaps: string[]
}

export interface Suggestion {
  id: number
  name_fr: string | null
  name_en: string
  sprite_url: string | null
  types: string[]
  score: number
  covers: string[]
}

export interface TeamAnalysis {
  team: TeamMember[]
  generation_used: number
  min_generation: number
  weaknesses: Weakness[]
  remaining_weaknesses: Weakness[]
  offensive_coverage: OffensiveCoverage
  suggestions: Suggestion[]
}

export async function analyzeTeam(
  pokemonIds: number[],
  generation?: number
): Promise<TeamAnalysis> {
  const res = await fetch(`${API_BASE}/team/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pokemon_ids: pokemonIds, generation }),
  })
  if (!res.ok) throw new Error(`team/analyze: ${res.status}`)
  return res.json()
}
