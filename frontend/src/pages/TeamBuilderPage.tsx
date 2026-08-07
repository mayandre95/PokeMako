import { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { analyzeTeam, type TeamAnalysis } from '../api/team'
import { PokemonSearchBar } from '../components/PokemonSearchBar'
import { TeamBuilder } from '../components/TeamBuilder'
import { TypeBadge } from '../components/TypeBadge'
import { TypeChart } from '../components/TypeChart'

const MAX_TEAM = 6

export default function TeamBuilderPage() {
  const [searchParams, setSearchParams] = useSearchParams()

  // Lecture depuis l'URL (?team=1,4,7) — liste compacte, sans emplacements vides
  const ids = (searchParams.get('team') ?? '')
    .split(',')
    .map(Number)
    .filter(Boolean)
    .slice(0, MAX_TEAM)
  const slots: (number | null)[] = [
    ...ids,
    ...Array(MAX_TEAM - ids.length).fill(null),
  ]

  const [analysis, setAnalysis] = useState<TeamAnalysis | null>(null)
  const [error, setError] = useState<string | null>(null)

  // null = suit automatiquement le minimum imposé par l'équipe (calculé par
  // le backend, `analysis.min_generation`) ; un choix explicite le fige.
  const [generationOverride, setGenerationOverride] = useState<number | null>(
    null
  )
  const minGeneration = analysis?.min_generation ?? 1
  const generation = generationOverride ?? minGeneration

  // Si l'équipe change et qu'un membre plus récent relève le plancher
  // au-dessus du choix explicite en cours, on retombe sur l'automatique
  // plutôt que d'envoyer une génération devenue invalide.
  useEffect(() => {
    if (generationOverride !== null && generationOverride < minGeneration) {
      setGenerationOverride(null)
    }
  }, [minGeneration, generationOverride])

  useEffect(() => {
    if (ids.length === 0) {
      setAnalysis(null)
      return
    }
    analyzeTeam(ids, generationOverride ?? undefined)
      .then((data) => {
        setAnalysis(data)
        setError(null)
      })
      .catch(() => setError("Impossible d'analyser cette équipe"))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ids.join(','), generationOverride])

  const updateSlots = (next: (number | null)[]) => {
    const compact = next.filter((id): id is number => id !== null)
    setSearchParams(compact.length ? { team: compact.join(',') } : {})
  }

  const addPokemon = (id: number) => {
    if (ids.includes(id) || ids.length >= MAX_TEAM) return
    updateSlots([...ids, id])
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <h1 className="text-2xl font-bold">Team Builder</h1>
      <Link to="/" className="text-blue-500 hover:underline text-sm">
        ← Retour
      </Link>

      <TeamBuilder
        slots={slots}
        team={analysis?.team ?? []}
        onChange={updateSlots}
      />

      <PokemonSearchBar
        onSelect={addPokemon}
        placeholder={
          ids.length >= MAX_TEAM ? 'Équipe complète' : 'Ajouter un Pokémon…'
        }
        disabled={ids.length >= MAX_TEAM}
      />

      {error && <p className="text-red-500">{error}</p>}

      {ids.length === 0 && (
        <p className="text-gray-400 text-center py-12">
          Ajoute un Pokémon pour commencer à construire ton équipe.
        </p>
      )}

      {analysis && (
        <>
          <section>
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold text-gray-700">
                Faiblesses cumulées
              </h2>
              <label className="flex items-center gap-2 text-sm text-gray-500">
                Génération
                <select
                  value={generation}
                  onChange={(e) =>
                    setGenerationOverride(Number(e.target.value))
                  }
                  className="border rounded px-2 py-1 text-sm"
                >
                  {Array.from(
                    { length: 9 - minGeneration + 1 },
                    (_, i) => minGeneration + i
                  ).map((g) => (
                    <option key={g} value={g}>
                      Gén. {g}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <p className="text-xs text-gray-400 mb-2">
              Nombre de membres vulnérables à chaque type, même si un teammate
              peut couvrir le trou.
            </p>
            {analysis.weaknesses.length === 0 ? (
              <p className="text-gray-400 italic text-sm">
                Aucune faiblesse détectée.
              </p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {analysis.weaknesses.map((w) => (
                  <span key={w.type} className="flex items-center gap-1">
                    <TypeBadge type={w.type} />
                    <span className="text-xs text-gray-500">
                      ×{w.weak_count}
                    </span>
                  </span>
                ))}
              </div>
            )}
          </section>

          <section>
            <h2 className="font-semibold text-gray-700 mb-1">
              Faiblesses restantes
            </h2>
            <p className="text-xs text-gray-400 mb-2">
              Celles des faiblesses cumulées pour lesquelles aucun membre ne
              résiste ni n'est immunisé — l'équipe n'a littéralement aucune
              réponse disponible.
            </p>
            {analysis.remaining_weaknesses.length === 0 ? (
              <p className="text-gray-400 italic text-sm">
                Chaque faiblesse cumulée est couverte par au moins un membre.
              </p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {analysis.remaining_weaknesses.map((w) => (
                  <span key={w.type} className="flex items-center gap-1">
                    <TypeBadge type={w.type} />
                    <span className="text-xs text-gray-500">
                      ×{w.weak_count}
                    </span>
                  </span>
                ))}
              </div>
            )}
          </section>

          <section>
            <h2 className="font-semibold text-gray-700 mb-3">
              Couverture offensive
            </h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-500 mb-1">Couverte</p>
                <div className="flex flex-wrap gap-1">
                  {analysis.offensive_coverage.covered.map((t) => (
                    <TypeBadge key={t} type={t} />
                  ))}
                </div>
              </div>
              <div>
                <p className="text-gray-500 mb-1">Lacunes</p>
                <div className="flex flex-wrap gap-1">
                  {analysis.offensive_coverage.gaps.map((t) => (
                    <TypeBadge key={t} type={t} />
                  ))}
                </div>
              </div>
            </div>
          </section>

          {ids.length < MAX_TEAM && analysis.suggestions.length > 0 && (
            <section>
              <h2 className="font-semibold text-gray-700 mb-3">Suggestions</h2>
              <div className="space-y-2">
                {analysis.suggestions.map((s) => (
                  <div
                    key={s.id}
                    className="flex items-center justify-between border rounded-lg p-3"
                  >
                    <div className="flex items-center gap-2">
                      {s.sprite_url && (
                        <img
                          src={s.sprite_url}
                          alt=""
                          width={40}
                          height={40}
                          style={{ imageRendering: 'pixelated' }}
                        />
                      )}
                      <div>
                        <p className="font-medium">{s.name_fr ?? s.name_en}</p>
                        <div className="flex gap-1">
                          {s.types.map((t) => (
                            <TypeBadge key={t} type={t} />
                          ))}
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => addPokemon(s.id)}
                      className="px-3 py-1 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700"
                    >
                      Ajouter
                    </button>
                  </div>
                ))}
              </div>
            </section>
          )}
        </>
      )}

      <details className="pt-4 border-t">
        <summary className="cursor-pointer font-semibold text-gray-700">
          Matrice générale des types
        </summary>
        <p className="text-xs text-gray-400 mt-2 mb-3">
          Référence indépendante de ton équipe — l'efficacité de chaque type
          contre chaque autre (ex. Feu est très efficace contre Plante mais
          faible contre Eau). En attendant une matrice spécifique à ton équipe
          (prévue plus tard).
        </p>
        <TypeChart />
      </details>
    </div>
  )
}
