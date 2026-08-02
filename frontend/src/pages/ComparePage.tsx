import { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import Plot from 'react-plotly.js'
import { fetchCompare, type CompareData } from '../api/compare'
import { TypeBadge } from '../components/TypeBadge'
import { PokemonSearchBar } from '../components/PokemonSearchBar'
import { STAT_LABELS } from '../constants/statLabels'
import { SCORE_LABELS } from '../constants/scoreLabels'

// Couleurs par position : indigo, rouge, vert
const COLORS = ['#6366f1', '#ef4444', '#22c55e']

export default function ComparePage() {
  const [searchParams, setSearchParams] = useSearchParams()

  // Lecture des IDs depuis l'URL (?p=1,4,7)
  const ids = (searchParams.get('p') ?? '')
    .split(',')
    .map(Number)
    .filter(Boolean)
    .slice(0, 3)

  const [pokemons, setPokemons] = useState<CompareData[]>([])

  // Chargement des données à chaque changement d'URL
  useEffect(() => {
    if (!ids.length) {
      setPokemons([])
      return
    }
    fetchCompare(ids).then(setPokemons).catch(console.error)
  }, [ids.join(',')])

  const addPokemon = (id: number) => {
    if (ids.includes(id) || ids.length >= 3) return
    setSearchParams({ p: [...ids, id].join(',') })
  }

  const removePokemon = (id: number) => {
    const next = ids.filter((i) => i !== id)
    next.length ? setSearchParams({ p: next.join(',') }) : setSearchParams({})
  }

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-8">
      <h1 className="text-2xl font-bold">Comparateur de Pokémon</h1>
      <div className="mb-2">
        <Link to="/" className="text-blue-500 hover:underline text-sm">
          ← Retour
        </Link>
      </div>
      {/* Barre de recherche autocomplete */}
      <PokemonSearchBar
        onSelect={addPokemon}
        placeholder={
          ids.length >= 3 ? 'Maximum 3 Pokémon' : 'Rechercher un Pokémon…'
        }
        disabled={ids.length >= 3}
      />

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
              r: [
                ...STAT_LABELS.map((s) => p[s.key] ?? 0),
                p[STAT_LABELS[0].key] ?? 0,
              ],
              theta: [...STAT_LABELS.map((s) => s.label), STAT_LABELS[0].label],
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
          <div>
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
                {SCORE_LABELS.map(({ labelShort, key, tooltip }) => (
                  <tr
                    key={key}
                    className="border-b last:border-0 hover:bg-gray-50"
                  >
                    <td className="py-2 pr-4 text-gray-500">
                      <span className="flex items-center gap-1">
                        {labelShort}
                        <span className="relative group cursor-default">
                          <span className="text-gray-400 text-xs">ⓘ</span>
                          <span className="absolute left-1/2 -translate-x-1/2 bottom-full mb-1.5 w-52 bg-gray-800 text-white text-xs rounded px-2 py-1.5 leading-snug opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                            {tooltip}
                            <span className="absolute left-1/2 -translate-x-1/2 top-full border-4 border-transparent border-t-gray-800" />
                          </span>
                        </span>
                      </span>
                    </td>
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
