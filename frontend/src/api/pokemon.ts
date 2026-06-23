const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
const POKEAPI = 'https://pokeapi.co/api/v2'

export interface Pokemon {
  id: number
  name: string
  name_en: string
  name_fr: string | null
  types: string[]
  generation: number | null
  hp: number | null
  attack: number | null
  defense: number | null
  sp_attack: number | null
  sp_defense: number | null
  speed: number | null
  base_experience: number | null
  height: number | null
  weight: number | null
  is_legendary: boolean
  is_mythical: boolean
  sprite_url: string | null
  artwork_url: string | null
}

export async function fetchPokemon(id: number | string): Promise<Pokemon> {
  const res = await fetch(`${API_BASE}/pokemon/${id}`)
  if (!res.ok) throw new Error(`Pokémon introuvable (HTTP ${res.status})`)
  return res.json()
}

// Texte Pokédex non stocké en DB — récupéré directement depuis PokéAPI
export async function fetchFlavorText(id: number): Promise<string> {
  const res = await fetch(`${POKEAPI}/pokemon-species/${id}`)
  if (!res.ok) return ''
  const data = await res.json()
  const entry = data.flavor_text_entries?.find(
    (e: { language: { name: string }; flavor_text: string }) =>
      e.language.name === 'fr'
  )
  return entry?.flavor_text?.replace(/\f/g, ' ') ?? ''
}
