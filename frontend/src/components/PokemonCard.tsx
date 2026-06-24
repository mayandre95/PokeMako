import { Pokemon } from '../api/pokemon'
import { TypeBadge } from './TypeBadge'
import { StatBar } from './StatBar'
import type { EvolutionNode } from '../api/pokemon'
import { EvolutionTree } from './EvolutionTree'

const STATS: { label: string; key: keyof Pokemon }[] = [
  { label: 'HP', key: 'hp' },
  { label: 'Attaque', key: 'attack' },
  { label: 'Défense', key: 'defense' },
  { label: 'Att. Spé', key: 'sp_attack' },
  { label: 'Déf. Spé', key: 'sp_defense' },
  { label: 'Vitesse', key: 'speed' },
]

interface Props {
  pokemon: Pokemon
  flavorText: string
  evolutionTree: EvolutionNode | null
}

export function PokemonCard({ pokemon, flavorText, evolutionTree }: Props) {
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
