import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import Plot from 'react-plotly.js'
import {
  fetchCompare,
  fetchSearch,
  type CompareData,
  type SearchResult,
} from '../api/compare'
import { TypeBadge } from '../components/TypeBadge'

// Couleurs par position : indigo, rouge, vert
const COLORS = ['#6366f1', '#ef4444', '#22c55e']
const RADAR_STATS = [
  'HP',
  'Attaque',
  'Défense',
  'Att.Spé',
  'Déf.Spé',
  'Vitesse',
] as const
const SCORE_ROWS = [
  { label: 'Power (BST)', key: 'power_score' },
  { label: 'Offensif', key: 'offensive_score' },
  { label: 'Défensif', key: 'tank_score' },
  { label: 'Méta', key: 'meta_score' },
] as const

export default function ComparePage() {
  const [searchParams, setSearchParams] = useSearchParams()

  // Lecture des IDs depuis l'URL (?p=1,4,7)
  const ids = (searchParams.get('p') ?? '')
    .split(',')
    .map(Number)
    .filter(Boolean)
    .slice(0, 3)

  const [pokemons, setPokemons] = useState<CompareData[]>([])
  const [query, setQuery] = useState('')
  const [suggestions, setSuggestions] = useState<SearchResult[]>([])
  const [showSugg, setShowSugg] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  // Chargement des données à chaque changement d'URL
  useEffect(() => {
    if (!ids.length) {
      setPokemons([])
      return
    }
    fetchCompare(ids).then(setPokemons).catch(console.error)
  }, [ids.join(',')])

  // Autocomplete avec debounce 300ms
  useEffect(() => {
    if (query.length < 2) {
      setSuggestions([])
      return
    }
    const timer = setTimeout(
      () => fetchSearch(query).then(setSuggestions).catch(console.error),
      300
    )
    return () => clearTimeout(timer)
  }, [query])

  const addPokemon = (id: number) => {
    if (ids.includes(id) || ids.length >= 3) return
    setSearchParams({ p: [...ids, id].join(',') })
    setQuery('')
    setSuggestions([])
  }

  const removePokemon = (id: number) => {
    const next = ids.filter((i) => i !== id)
    next.length ? setSearchParams({ p: next.join(',') }) : setSearchParams({})
  }

  // Données radar : on répète le premier point pour fermer le polygone
  const statKeys = [
    'hp',
    'attack',
    'defense',
    'sp_attack',
    'sp_defense',
    'speed',
  ] as const

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-8">
      <h1 className="text-2xl font-bold">Comparateur de Pokémon</h1>

      {/* Barre de recherche autocomplete */}
      <div className="relative">
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            setShowSugg(true)
          }}
          onFocus={() => setShowSugg(true)}
          onBlur={() => setTimeout(() => setShowSugg(false), 150)}
          placeholder={
            ids.length >= 3 ? 'Maximum 3 Pokémon' : 'Rechercher un Pokémon…'
          }
          disabled={ids.length >= 3}
          className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:opacity-50"
        />
        {showSugg && suggestions.length > 0 && (
          <ul className="absolute z-10 w-full bg-white border rounded-lg shadow-lg mt-1 max-h-60 overflow-y-auto">
            {suggestions.map((s) => (
              <li
                key={s.id}
                onMouseDown={() => addPokemon(s.id)}
                className="flex items-center gap-2 px-3 py-2 hover:bg-gray-100 cursor-pointer"
              >
                {s.sprite_url && (
                  <img
                    src={s.sprite_url}
                    alt=""
                    width={32}
                    height={32}
                    style={{ imageRendering: 'pixelated' }}
                  />
                )}
                <span className="font-medium">{s.name_fr ?? s.name_en}</span>
                <span className="text-gray-400 text-xs">#{s.id}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Pokémon sélectionnés (chips) */}
      {ids.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {pokemons.map((p, i) => (
            <span
              key={p.id}
              className="flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium text-white"
              style={{ backgroundColor: COLORS[i] }}
            >
              {p.name_fr ?? p.name_en}
              <button
                onClick={() => removePokemon(p.id)}
                className="ml-1 hover:opacity-70 font-bold"
                aria-label={`Retirer ${p.name_fr ?? p.name_en}`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Radar chart */}
      {pokemons.length > 0 && (
        <section>
          <h2 className="font-semibold text-gray-700 mb-3">Statistiques</h2>
          <Plot
            data={pokemons.map((p, i) => ({
              type: 'scatterpolar' as const,
              r: [...statKeys.map((k) => p[k] ?? 0), p[statKeys[0]] ?? 0],
              theta: [...RADAR_STATS, RADAR_STATS[0]],
              fill: 'toself' as const,
              name: p.name_fr ?? p.name_en,
              line: { color: COLORS[i] },
              opacity: 0.75,
            }))}
            layout={{
              polar: {
                radialaxis: {
                  range: [0, 255],
                  visible: true,
                  tickfont: { size: 10 },
                },
              },
              showlegend: true,
              height: 380,
              margin: { t: 30, b: 30, l: 40, r: 40 },
              legend: { orientation: 'h', y: -0.15 },
            }}
            config={{ displayModeBar: false }}
            useResizeHandler
            style={{ width: '100%' }}
          />
        </section>
      )}

      {/* Tableau de comparaison des scores */}
      {pokemons.length > 0 && (
        <section>
          <h2 className="font-semibold text-gray-700 mb-3">
            Scores analytiques
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 pr-4 font-medium text-gray-500">
                    Score
                  </th>
                  {pokemons.map((p, i) => (
                    <th
                      key={p.id}
                      className="py-2 px-4 font-semibold"
                      style={{ color: COLORS[i] }}
                    >
                      <div className="flex flex-col items-center gap-1">
                        {p.sprite_url && (
                          <img
                            src={p.sprite_url}
                            alt=""
                            width={40}
                            height={40}
                            style={{ imageRendering: 'pixelated' }}
                          />
                        )}
                        {p.name_fr ?? p.name_en}
                        <div className="flex gap-1 flex-wrap justify-center">
                          {p.types.map((t) => (
                            <TypeBadge key={t} type={t} />
                          ))}
                        </div>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {SCORE_ROWS.map(({ label, key }) => (
                  <tr
                    key={key}
                    className="border-b last:border-0 hover:bg-gray-50"
                  >
                    <td className="py-2 pr-4 text-gray-500">{label}</td>
                    {pokemons.map((p) => (
                      <td
                        key={p.id}
                        className="py-2 px-4 text-center font-mono font-medium"
                      >
                        {p[key] ?? '—'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* État vide */}
      {ids.length === 0 && (
        <p className="text-gray-400 text-center py-12">
          Recherche un Pokémon pour commencer la comparaison.
        </p>
      )}
    </div>
  )
}
