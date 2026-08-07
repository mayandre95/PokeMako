import { useState, useMemo, useEffect } from 'react'
import { Link } from 'react-router-dom'
import type { Move } from '../api/pokemon'
import { TypeBadge } from './TypeBadge'
import {
  LEARN_METHOD_FR,
  DAMAGE_CLASS_FR,
  DAMAGE_CLASS_COLORS,
} from '../constants/methodNames'
import { VERSION_GROUP_FR, sortVersionGroups } from '../constants/gameNames'

const METHOD_ORDER = ['level-up', 'machine', 'egg', 'tutor']

interface Props {
  moves: Move[]
  onVersionGroupChange?: (vg: string) => void
}

export function MovesTable({ moves, onVersionGroupChange }: Props) {
  const methods = useMemo(
    () => METHOD_ORDER.filter((m) => moves.some((mv) => mv.method === m)),
    [moves]
  )

  const [selectedMethod, setSelectedMethod] = useState<string>(methods[0] ?? '')

  const versionGroups = useMemo(
    () =>
      sortVersionGroups([
        ...new Set(
          moves
            .filter((m) => m.method === selectedMethod)
            .map((m) => m.version_group)
        ),
      ]),
    [moves, selectedMethod]
  )

  const [selectedVg, setSelectedVg] = useState<string>('')
  const activeVg =
    selectedVg && versionGroups.includes(selectedVg)
      ? selectedVg
      : (versionGroups[versionGroups.length - 1] ?? '')

  useEffect(() => {
    onVersionGroupChange?.(activeVg)
  }, [activeVg, onVersionGroupChange])

  const filtered = moves.filter(
    (m) => m.method === selectedMethod && m.version_group === activeVg
  )

  if (moves.length === 0) {
    return (
      <p className="text-sm text-gray-500 italic">
        Aucune attaque connue pour ce Pokémon.
      </p>
    )
  }

  return (
    <div>
      {/* Onglets méthode */}
      <div className="flex flex-wrap gap-2 mb-4">
        {methods.map((m) => (
          <button
            key={m}
            onClick={() => {
              setSelectedMethod(m)
              setSelectedVg('')
            }}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
              selectedMethod === m
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {LEARN_METHOD_FR[m] ?? m}
          </button>
        ))}
      </div>

      {/* Filtre par version */}
      <div className="flex flex-wrap gap-1 mb-3">
        {versionGroups.map((vg) => (
          <button
            key={vg}
            onClick={() => setSelectedVg(vg)}
            className={`px-2 py-0.5 rounded text-xs transition-colors ${
              activeVg === vg
                ? 'bg-gray-700 text-white'
                : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
            }`}
          >
            {VERSION_GROUP_FR[vg] ?? vg}
          </button>
        ))}
      </div>

      {/* Tableau */}
      {filtered.length === 0 ? (
        <p className="text-sm text-gray-400 italic">
          Aucune attaque pour cette sélection.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead>
              <tr className="text-gray-500 border-b text-xs uppercase">
                {selectedMethod === 'level-up' && (
                  <th className="pb-2 pr-3">Niv.</th>
                )}
                <th className="pb-2 pr-3">Nom</th>
                <th className="pb-2 pr-3">Type</th>
                <th className="pb-2 pr-3">Cat.</th>
                <th className="pb-2 pr-3">Puiss.</th>
                <th className="pb-2 pr-3">Précis.</th>
                <th className="pb-2">PP</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((mv, i) => (
                <tr
                  key={i}
                  className="border-b border-gray-50 hover:bg-gray-50"
                >
                  {selectedMethod === 'level-up' && (
                    <td className="py-2 pr-3 text-gray-500 text-xs w-10">
                      {mv.level_learned > 0 ? mv.level_learned : '—'}
                    </td>
                  )}
                  <td className="py-2 pr-3 font-medium text-gray-800">
                    <Link
                      to={`/move/${mv.id}`}
                      className="hover:text-blue-500 hover:underline"
                    >
                      {mv.name_fr ?? mv.name_en}
                    </Link>
                  </td>
                  <td className="py-2 pr-3">
                    <TypeBadge type={mv.type} />
                  </td>
                  <td className="py-2 pr-3">
                    <span
                      className="px-2 py-0.5 rounded text-white text-xs font-medium"
                      style={{
                        backgroundColor:
                          DAMAGE_CLASS_COLORS[mv.damage_class] ?? '#888',
                      }}
                    >
                      {DAMAGE_CLASS_FR[mv.damage_class] ?? mv.damage_class}
                    </span>
                  </td>
                  <td className="py-2 pr-3 text-gray-600 text-center w-12">
                    {mv.power ?? '—'}
                  </td>
                  <td className="py-2 pr-3 text-gray-600 text-center w-14">
                    {mv.accuracy != null ? `${mv.accuracy} %` : '—'}
                  </td>
                  <td className="py-2 text-gray-600 text-center w-10">
                    {mv.pp ?? '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
