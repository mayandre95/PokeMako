const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export interface SearchResult {
  id: number
  name_fr: string | null
  name_en: string
  sprite_url: string | null
}

export const fetchSearch = (q: string): Promise<SearchResult[]> =>
  fetch(`${API}/search?q=${encodeURIComponent(q)}&limit=8`).then((r) =>
    r.json()
  )
