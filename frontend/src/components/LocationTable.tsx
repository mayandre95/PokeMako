import { useState, useMemo } from 'react'
import type { Encounter } from '../api/pokemon'
import {
  GAME_FR,
  GAME_ORDER,
  GAME_REGION,
  REGION_BULBAPEDIA,
} from '../constants/gameNames'
import {
  METHOD_FR,
  CONDITION_FR,
  isPositiveCondition,
} from '../constants/methodNames'
import { LOCATION_AREA_FR } from '../constants/locationAreaNames'

function formatArea(name: string): string {
  const REGIONS = 'kanto|johto|hoenn|sinnoh|unova|kalos|alola|galar|paldea'

  // Routes maritimes : kanto-sea-route-19-area → "Route Maritime 19"
  const seaRoute = name.match(
    new RegExp(`^(?:${REGIONS})-sea-route-(\\d+)(?:-.+)?$`)
  )
  if (seaRoute) return `Route Maritime ${seaRoute[1]}`

  // Routes standard : region-route-N(-suffix)
  const stdRoute = name.match(
    new RegExp(`^(?:${REGIONS})-route-(\\d+)(?:-(.+))?$`)
  )
  if (stdRoute) {
    const n = stdRoute[1]
    const suffix = stdRoute[2] ?? ''
    if (suffix.startsWith('pokemon-center'))
      return `Centre Pokémon (Route ${n})`
    if (suffix === 'east') return `Route ${n} (Est)`
    if (suffix === 'west') return `Route ${n} (Ouest)`
    if (suffix.startsWith('north')) return `Route ${n} (Nord)`
    if (suffix.startsWith('south')) return `Route ${n} (Sud)`
    if (suffix === 'lakeside') return `Route ${n} (Lac)`
    return `Route ${n}`
  }

  // Safari Ami par type : friend-safari-electric → "Safari Ami"
  if (name.startsWith('friend-safari-')) return 'Safari Ami'

  return name
    .replace(/-(?:area|main)$/, '') // supprime suffixe final -area ou -main
    .split('-')
    .filter((w) => w !== 'area')
    .map((w) => {
      if (/^b\d+f$/.test(w)) return w.replace(/^b(\d+)f$/, 'B$1') // b3f → B3
      if (/^\d+f$/.test(w)) return w.toUpperCase() // 1f → 1F
      return w.charAt(0).toUpperCase() + w.slice(1)
    })
    .join(' ')
}

interface Props {
  encounters: Encounter[]
}

export function LocationTable({ encounters }: Props) {
  const games = useMemo(() => {
    const unique = [...new Set(encounters.map((e) => e.game))]
    return unique.sort((a, b) => {
      const ia = GAME_ORDER.indexOf(a)
      const ib = GAME_ORDER.indexOf(b)
      if (ia === -1 && ib === -1) return a.localeCompare(b)
      if (ia === -1) return 1
      if (ib === -1) return -1
      return ia - ib
    })
  }, [encounters])
  const [selectedGame, setSelectedGame] = useState<string>(games[0] ?? '')

  const filtered = encounters.filter((e) => e.game === selectedGame)
  const region = GAME_REGION[selectedGame]
  const mapUrl = region ? REGION_BULBAPEDIA[region] : null

  if (encounters.length === 0) {
    return (
      <p className="text-sm text-gray-500 italic">
        Ce Pokémon n'est pas trouvable dans la nature — il s'obtient par échange
        ou évolution.
      </p>
    )
  }

  return (
    <div>
      {/* Filtre par jeu */}
      <div className="flex flex-wrap gap-2 mb-4">
        {games.map((game) => (
          <button
            key={game}
            onClick={() => setSelectedGame(game)}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
              selectedGame === game
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {GAME_FR[game] ?? game}
          </button>
        ))}
      </div>

      {/* Région + lien carte */}
      {region && (
        <div className="flex items-center gap-2 mb-3 text-sm text-gray-500">
          <span>
            Région : <strong className="text-gray-700">{region}</strong>
          </span>
          {mapUrl && (
            <a
              href={mapUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-500 hover:underline"
            >
              Voir la carte →
            </a>
          )}
        </div>
      )}

      {/* Tableau des rencontres */}
      {filtered.length === 0 ? (
        <p className="text-sm text-gray-400 italic">
          Pas de rencontre sauvage dans ce jeu.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead>
              <tr className="text-gray-500 border-b text-xs uppercase">
                <th className="pb-2 pr-4">Zone</th>
                <th className="pb-2 pr-4">Méthode</th>
                <th className="pb-2 pr-4">Chance</th>
                <th className="pb-2 pr-4">Niveaux</th>
                <th className="pb-2">Conditions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((e, i) => (
                <tr
                  key={i}
                  className="border-b border-gray-50 hover:bg-gray-50"
                >
                  <td className="py-2 pr-4 font-medium text-gray-700">
                    {e.location_area_fr ??
                      LOCATION_AREA_FR[e.location_area] ??
                      formatArea(e.location_area)}
                  </td>
                  <td className="py-2 pr-4 text-gray-600">
                    {METHOD_FR[e.method] ?? e.method}
                  </td>
                  <td className="py-2 pr-4 text-gray-600">
                    {e.chance > 0 ? `${e.chance} %` : '—'}
                  </td>
                  <td className="py-2 pr-4 text-gray-600">
                    {e.min_level === e.max_level
                      ? `Niv. ${e.min_level}`
                      : `Niv. ${e.min_level}–${e.max_level}`}
                  </td>
                  <td className="py-2 text-gray-500 text-xs">
                    {(() => {
                      const pos = e.conditions.filter(isPositiveCondition)
                      return pos.length > 0
                        ? pos.map((c) => CONDITION_FR[c] ?? c).join(', ')
                        : '—'
                    })()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="mt-3 text-xs text-gray-400 italic">
        Seules les rencontres sauvages, les starters et les cadeaux liés au
        scénario principal sont affichées. Dans les jeux absents de cette liste,
        ce Pokémon s'obtient autrement (cadeau PNJ, échange, etc.).
      </p>
    </div>
  )
}
