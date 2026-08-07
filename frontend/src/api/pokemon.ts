import type { RoleKey } from '../constants/roleLabels'

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

export interface EvolutionCondition {
  trigger: string
  min_level: number | null
  item: string | null
  held_item: string | null
  min_happiness: number | null
  time_of_day: string
  location: string | null
  known_move_type: string | null
}

export interface EvolutionNode {
  id: number
  name: string
  sprite_url: string
  conditions: EvolutionCondition[]
  evolves_to: EvolutionNode[]
}

export async function fetchPokemon(id: number | string): Promise<Pokemon> {
  const res = await fetch(`${API_BASE}/pokemon/${id}`)
  if (!res.ok) throw new Error(`Pokémon introuvable (HTTP ${res.status})`)
  return res.json()
}

export interface Encounter {
  location_area: string
  location_area_fr?: string
  game: string
  method: string
  chance: number
  min_level: number
  max_level: number
  conditions: string[]
}

export interface EncountersData {
  encounters: Encounter[]
  has_encounters: boolean
}

export interface Move {
  id: number
  method: string
  level_learned: number
  version_group: string
  name_fr: string | null
  name_en: string
  type: string
  damage_class: string
  power: number | null
  accuracy: number | null
  pp: number | null
}

export interface MovesData {
  moves: Move[]
}

export interface MoveDetail {
  id: number
  name_fr: string | null
  name_en: string
  type: string
  damage_class: string
  power: number | null
  accuracy: number | null
  pp: number | null
  effect_fr: string | null
  effect_en: string | null
}

export interface ScoresData {
  pokemon_id: number
  power_score: number
  offensive_score: number
  tank_score: number
  meta_score: number
  generation_used: number
  attacker_score: number
  tank_role_score: number
  support_score: number
  sweeper_score: number
  versatility_score: number
  dominant_role: RoleKey
}

export interface ScoreHistoryPoint {
  generation: number
  meta_score: number
  active: boolean
}

export interface RecommendedMove {
  id: number
  name_fr: string | null
  name_en: string
  type: string
  damage_class: string
  power: number | null
  accuracy: number | null
  pp: number | null
  method: string
  method_label: string | null
  version_group: string
  dps: number
  types_covered: number
  reason: string
}

export interface MovesetResult {
  role: string
  version_group: string
  moves: RecommendedMove[]
}

export async function fetchMovesetRecommendation(
  id: number,
  role: string,
  versionGroup: string,
  excludeHm: boolean,
  excludeTm: boolean
): Promise<MovesetResult> {
  const res = await fetch(`${API_BASE}/pokemon/${id}/recommend-moveset`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      role,
      version_group: versionGroup,
      exclude_hm: excludeHm,
      exclude_tm: excludeTm,
    }),
  })
  if (!res.ok) throw new Error(`recommend-moveset ${id}: ${res.status}`)
  return res.json()
}

export async function fetchScoreHistory(
  id: number
): Promise<ScoreHistoryPoint[]> {
  const res = await fetch(`${API_BASE}/pokemon/${id}/scores/history`)
  if (!res.ok) throw new Error(`scores history ${id}: ${res.status}`)
  return res.json()
}

export async function fetchScores(
  id: number,
  generation?: number
): Promise<ScoresData> {
  const url = generation
    ? `${API_BASE}/pokemon/${id}/scores?generation=${generation}`
    : `${API_BASE}/pokemon/${id}/scores`
  const res = await fetch(url)
  if (!res.ok) throw new Error(`scores ${id}: ${res.status}`)
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

interface RawChainLink {
  species: { name: string; url: string }
  evolution_details: Array<{
    trigger: { name: string }
    min_level: number | null
    item: { name: string } | null
    held_item: { name: string } | null
    min_happiness: number | null
    time_of_day: string
    location: { name: string } | null
    known_move_type: { name: string } | null
  }>
  evolves_to: RawChainLink[]
}

function parseChain(link: RawChainLink): EvolutionNode {
  const id = Number(link.species.url.split('/').filter(Boolean).pop())

  // Si une Pierre (use-item) coexiste avec des méthodes par lieu (level-up + location),
  // on supprime les conditions de lieu : ce sont des méthodes Gen 4-7 remplacées
  // par des Pierres en Gen 8+. Sans ce filtre, Phyllali/Givrali afficheraient
  // ~6 branches (5 lieux + la pierre) au lieu d'une seule.
  const raw = link.evolution_details
  const hasUseItem = raw.some((d) => d.trigger.name === 'use-item')
  const hasLevelUpLocation = raw.some(
    (d) => d.trigger.name === 'level-up' && d.location
  )
  const details =
    hasUseItem && hasLevelUpLocation
      ? raw.filter((d) => !(d.trigger.name === 'level-up' && d.location))
      : raw

  return {
    id,
    name: link.species.name,
    sprite_url: `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${id}.png`,
    conditions: details.map((d) => ({
      trigger: d.trigger.name,
      min_level: d.min_level,
      item: d.item?.name ?? null,
      held_item: d.held_item?.name ?? null,
      min_happiness: d.min_happiness,
      time_of_day: d.time_of_day,
      location: d.location?.name ?? null,
      known_move_type: d.known_move_type?.name ?? null,
    })),
    evolves_to: link.evolves_to.map(parseChain),
  }
}

function collectIds(node: EvolutionNode): number[] {
  return [node.id, ...node.evolves_to.flatMap(collectIds)]
}

function applyNames(
  node: EvolutionNode,
  nameMap: Map<number, string>
): EvolutionNode {
  return {
    ...node,
    name: nameMap.get(node.id) ?? node.name,
    evolves_to: node.evolves_to.map((child) => applyNames(child, nameMap)),
  }
}

export async function fetchEvolutionChain(
  id: number
): Promise<EvolutionNode | null> {
  const speciesRes = await fetch(`${POKEAPI}/pokemon-species/${id}`)
  if (!speciesRes.ok) return null
  const species = await speciesRes.json()
  const chainRes = await fetch(species.evolution_chain.url)
  if (!chainRes.ok) return null
  const chain = await chainRes.json()
  const tree = parseChain(chain.chain)

  const ids = collectIds(tree)
  const pokemonList = await Promise.all(
    ids.map((pid) => fetchPokemon(pid).catch(() => null))
  )
  const nameMap = new Map(
    pokemonList.filter(Boolean).map((p) => [p!.id, p!.name_fr ?? p!.name_en])
  )
  return applyNames(tree, nameMap)
}

export async function fetchEncounters(id: number): Promise<EncountersData> {
  const res = await fetch(`${API_BASE}/pokemon/${id}/encounters`)
  if (!res.ok) return { encounters: [], has_encounters: false }
  return res.json()
}

export async function fetchMoves(id: number): Promise<MovesData> {
  const res = await fetch(`${API_BASE}/pokemon/${id}/moves`)
  if (!res.ok) return { moves: [] }
  return res.json()
}

export async function fetchMoveDetail(id: number): Promise<MoveDetail | null> {
  const res = await fetch(`${API_BASE}/move/${id}`)
  if (!res.ok) return null
  return res.json()
}
