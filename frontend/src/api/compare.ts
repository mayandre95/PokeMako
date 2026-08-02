const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export interface SearchResult {
  id: number
  name_fr: string | null
  name_en: string
  sprite_url: string | null
}

export interface CompareData {
  id: number
  name_fr: string | null
  name_en: string
  sprite_url: string | null
  types: string[]
  hp: number | null
  attack: number | null
  defense: number | null
  sp_attack: number | null
  sp_defense: number | null
  speed: number | null
  power_score: number | null
  offensive_score: number | null
  tank_score: number | null
  meta_score: number | null
}

export const fetchSearch = (q: string): Promise<SearchResult[]> =>
  fetch(`${API}/search?q=${encodeURIComponent(q)}&limit=8`).then((r) =>
    r.json()
  )

export const fetchCompare = (ids: number[]): Promise<CompareData[]> =>
  fetch(`${API}/compare?ids=${ids.join(',')}`).then((r) => r.json())
