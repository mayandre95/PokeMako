import { useEffect, useState } from 'react'
import {
  fetchMovesetRecommendation,
  type RecommendedMove,
} from '../api/pokemon'
import { TypeBadge } from './TypeBadge'
import { DAMAGE_CLASS_FR, DAMAGE_CLASS_COLORS } from '../constants/methodNames'
import { MOVESET_ROLE_OPTIONS } from '../constants/roleLabels'

interface Props {
  pokemonId: number
  versionGroup: string
}

export function MovesetRecommendation({ pokemonId, versionGroup }: Props) {
  const [excludeHm, setExcludeHm] = useState(false)
  const [excludeTm, setExcludeTm] = useState(false)
  const [role, setRole] = useState<string | null>(null)
  const [result, setResult] = useState<RecommendedMove[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const recommend = (nextRole: string) => {
    if (!versionGroup) return
    setLoading(true)
    setError(null)
    fetchMovesetRecommendation(
      pokemonId,
      nextRole,
      versionGroup,
      excludeHm,
      excludeTm
    )
      .then((res) => setResult(res.moves))
      .catch(() => setError('Impossible de calculer le moveset recommandé'))
      .finally(() => setLoading(false))
  }

  const handleRole = (nextRole: string) => {
    setRole(nextRole)
    recommend(nextRole)
  }

  // Rejoue la recommandation si la version (choisie dans MovesTable, remontée
  // par le parent) ou l'un des deux filtres changent — uniquement si un rôle a
  // déjà été choisi une première fois.
  useEffect(() => {
    if (role) recommend(role)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [versionGroup, excludeHm, excludeTm])

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3 mb-3">
        <label className="flex items-center gap-1 text-xs text-gray-600">
          <input
            type="checkbox"
            checked={excludeHm}
            onChange={(e) => setExcludeHm(e.target.checked)}
          />
          Sans CS
        </label>
        <label className="flex items-center gap-1 text-xs text-gray-600">
          <input
            type="checkbox"
            checked={excludeTm}
            onChange={(e) => setExcludeTm(e.target.checked)}
          />
          Sans CT
        </label>
      </div>

      <div className="flex flex-wrap gap-1 mb-3">
        {MOVESET_ROLE_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => handleRole(opt.value)}
            className="px-2 py-0.5 rounded text-xs font-medium transition-colors"
            style={
              role === opt.value
                ? { backgroundColor: opt.color, color: 'white' }
                : undefined
            }
          >
            {opt.label}
          </button>
        ))}
      </div>

      {loading && (
        <p className="text-sm text-gray-400 italic">Calcul en cours…</p>
      )}
      {error && <p className="text-sm text-red-500">{error}</p>}

      {result && (
        <ul className="space-y-2">
          {result.map((m) => (
            <li key={m.id} className="border rounded-lg p-3">
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <span className="font-medium text-gray-800">
                  {m.name_fr ?? m.name_en}
                </span>
                <TypeBadge type={m.type} />
                <span
                  className="px-2 py-0.5 rounded text-white text-xs font-medium"
                  style={{
                    backgroundColor:
                      DAMAGE_CLASS_COLORS[m.damage_class] ?? '#888',
                  }}
                >
                  {DAMAGE_CLASS_FR[m.damage_class] ?? m.damage_class}
                </span>
                {m.method_label && (
                  <span className="px-2 py-0.5 rounded bg-gray-700 text-white text-xs font-medium">
                    {m.method_label}
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-500">{m.reason}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
