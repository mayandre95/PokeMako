import { Pokemon } from '../api/pokemon'
import { TypeBadge } from './TypeBadge'
import { StatBar } from './StatBar'
import type {
  EncountersData,
  EvolutionNode,
  MovesData,
  ScoresData,
  ScoreHistoryPoint,
} from '../api/pokemon'
import { EvolutionTree } from './EvolutionTree'
import { LocationTable } from './LocationTable'
import { MovesTable } from './MovesTable'
import { ScoreBar } from './ScoreBar'
import Plot from 'react-plotly.js'

function groupHistory(history: ScoreHistoryPoint[]) {
  const active = history.filter((p) => p.active)
  if (active.length === 0) return []
  const groups: { label: string; meta_score: number }[] = []
  let start = active[0].generation
  let score = active[0].meta_score
  for (let i = 1; i < active.length; i++) {
    if (active[i].meta_score !== score) {
      const end = active[i - 1].generation
      groups.push({
        label: start === end ? `Gen ${start}` : `Gen ${start} à ${end}`,
        meta_score: score,
      })
      start = active[i].generation
      score = active[i].meta_score
    }
  }
  const last = active[active.length - 1].generation
  groups.push({
    label: start === last ? `Gen ${start}` : `Gen ${start} à ${last}`,
    meta_score: score,
  })
  return groups
}

const STATS: { label: string; key: keyof Pokemon }[] = [
  { label: 'HP', key: 'hp' },
  { label: 'Attaque', key: 'attack' },
  { label: 'Défense', key: 'defense' },
  { label: 'Att. Spé', key: 'sp_attack' },
  { label: 'Déf. Spé', key: 'sp_defense' },
  { label: 'Vitesse', key: 'speed' },
]

const GENS = [1, 2, 3, 4, 5, 6, 7, 8, 9]

interface Props {
  pokemon: Pokemon
  flavorText: string
  evolutionTree: EvolutionNode | null
  encountersData: EncountersData | null
  movesData: MovesData | null
  scoresData: ScoresData | null
  selectedGeneration: number | null
  onGenerationChange: (gen: number | null) => void
  scoreHistory: ScoreHistoryPoint[]
}

export function PokemonCard({
  pokemon,
  flavorText,
  evolutionTree,
  encountersData,
  movesData,
  scoresData,
  selectedGeneration,
  scoreHistory,
  onGenerationChange,
}: Props) {
  const displayName = pokemon.name_fr ?? pokemon.name_en
  const numStr = String(pokemon.id).padStart(4, '0')

  return (
    <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-lg p-6">
      {/* En-tête */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="text-gray-400 text-sm">#{numStr}</p>
          <h1 className="text-3xl font-bold capitalize">{displayName}</h1>
          <p className="text-gray-400 text-sm">
            Génération {pokemon.generation}
            {pokemon.is_legendary && ' · Légendaire'}
            {pokemon.is_mythical && ' · Mythique'}
          </p>
        </div>
        <div className="flex gap-2 flex-wrap justify-end">
          {pokemon.types.map((t) => (
            <TypeBadge key={t} type={t} />
          ))}
        </div>
      </div>

      {/* Images */}
      <div className="flex justify-center gap-8 my-6">
        {pokemon.sprite_url && (
          <img
            src={pokemon.sprite_url}
            alt={`Sprite ${displayName}`}
            width={96}
            height={96}
            loading="lazy"
            style={{ imageRendering: 'pixelated' }}
          />
        )}
        {pokemon.artwork_url && (
          <img
            src={pokemon.artwork_url}
            alt={`Artwork officiel de ${displayName}`}
            className="w-48 h-48 object-contain"
            loading="lazy"
          />
        )}
      </div>

      {/* Description Pokédex */}
      {flavorText && (
        <p className="text-gray-600 italic text-sm text-center mb-6 px-4 leading-relaxed">
          {flavorText}
        </p>
      )}

      {/* Stats */}
      <section aria-label="Statistiques de base">
        <h2 className="font-semibold text-gray-700 mb-3">
          Statistiques de base
        </h2>
        <div className="space-y-2">
          {STATS.map(({ label, key }) => (
            <StatBar
              key={key}
              label={label}
              value={pokemon[key] as number | null}
            />
          ))}
        </div>
      </section>

      {evolutionTree && (
        <section aria-label="Chaîne d'évolution" className="mt-6">
          <h2 className="font-semibold text-gray-700 mb-3">
            Chaîne d'évolution
          </h2>
          <EvolutionTree root={evolutionTree} currentId={pokemon.id} />
        </section>
      )}

      {encountersData && (
        <section aria-label="Localisations" className="mt-6">
          <h2 className="font-semibold text-gray-700 mb-3">
            Où trouver ce Pokémon ?
          </h2>
          <LocationTable encounters={encountersData.encounters} />
        </section>
      )}

      {movesData && movesData.moves.length > 0 && (
        <section aria-label="Attaques" className="mt-6">
          <h2 className="font-semibold text-gray-700 mb-3">Attaques</h2>
          <MovesTable moves={movesData.moves} />
        </section>
      )}

      {scoresData && (
        <section aria-label="Scores analytiques" className="mt-6">
          <h2 className="font-semibold text-gray-700 mb-3">
            Scores analytiques
          </h2>
          <div className="flex flex-wrap gap-1 mb-3">
            <button
              onClick={() => onGenerationChange(null)}
              className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
                selectedGeneration === null
                  ? 'bg-gray-700 text-white'
                  : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
              }`}
            >
              Natif (Gen {pokemon.generation})
            </button>
            {GENS.map((g) => (
              <button
                key={g}
                onClick={() => onGenerationChange(g)}
                className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
                  selectedGeneration === g
                    ? 'bg-indigo-500 text-white'
                    : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                }`}
              >
                Gen {g}
              </button>
            ))}
          </div>
          <div className="space-y-3">
            <ScoreBar
              label="Score total (BST)"
              value={scoresData.power_score}
              max={800}
              color="#6366f1"
              tooltip="Somme des 6 statistiques de base : PV + Attaque + Défense + Att. Spé + Déf. Spé + Vitesse"
            />
            <ScoreBar
              label="Score offensif"
              value={scoresData.offensive_score}
              max={450}
              color="#ef4444"
              tooltip="Capacité à attaquer vite et fort : Attaque + Att. Spé + Vitesse"
            />
            <ScoreBar
              label="Score défensif"
              value={scoresData.tank_score}
              max={450}
              color="#22c55e"
              tooltip="Résistance aux dégâts : PV + Défense + Déf. Spé"
            />
            <ScoreBar
              label="Score méta"
              value={scoresData.meta_score}
              max={900}
              color="#f59e0b"
              tooltip="Score total ajusté selon les résistances et faiblesses de type : +10 par immunité, +5 par résistance, −10 par faiblesse"
            />
            {scoreHistory.length > 0 &&
              (() => {
                const groups = groupHistory(scoreHistory)
                return (
                  groups.length > 0 && (
                    <div className="mt-4">
                      <Plot
                        data={[
                          {
                            type: 'bar',
                            x: groups.map((g) => g.label),
                            y: groups.map((g) => g.meta_score),
                            width: groups.map(() => 0.15),
                            marker: { color: '#f59e0b' },
                            hovertemplate:
                              '<b>%{x}</b><br>Score méta : %{y}<extra></extra>',
                          },
                        ]}
                        layout={{
                          autosize: true,
                          height: 220,
                          margin: { t: 10, b: 40, l: 50, r: 10 },
                          xaxis: { fixedrange: true },
                          yaxis: { title: 'Score méta', fixedrange: true },
                        }}
                        config={{ displayModeBar: false }}
                        useResizeHandler
                        style={{ width: '100%' }}
                      />
                    </div>
                  )
                )
              })()}
          </div>
          <p className="mt-2 text-xs text-gray-400 italic">
            Score méta calculé avec le méta Gen {scoresData.generation_used}
          </p>
        </section>
      )}

      {/* Infos physiques */}
      <div className="flex justify-around mt-6 text-center text-sm text-gray-600 border-t pt-4">
        <div>
          <p className="font-semibold">
            {((pokemon.height ?? 0) / 10).toFixed(1)} m
          </p>
          <p>Taille</p>
        </div>
        <div>
          <p className="font-semibold">
            {((pokemon.weight ?? 0) / 10).toFixed(1)} kg
          </p>
          <p>Poids</p>
        </div>
        <div>
          <p className="font-semibold">{pokemon.base_experience ?? '—'}</p>
          <p>Exp. de base</p>
        </div>
      </div>
    </div>
  )
}
