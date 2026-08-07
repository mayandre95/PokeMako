import { useState } from 'react'
import type { TeamMember } from '../api/team'
import { TYPE_COLORS, TYPE_FR } from '../constants/typeColors'

interface Props {
  slots: (number | null)[] // toujours longueur 6
  team: TeamMember[]
  onChange: (slots: (number | null)[]) => void
}

export function TeamBuilder({ slots, team, onChange }: Props) {
  const teamMap = new Map(team.map((p) => [p.id, p]))
  const [dragIndex, setDragIndex] = useState<number | null>(null)

  const handleDrop = (targetIndex: number) => {
    if (dragIndex === null || dragIndex === targetIndex) return
    const next = [...slots]
    ;[next[dragIndex], next[targetIndex]] = [next[targetIndex], next[dragIndex]]
    onChange(next)
    setDragIndex(null)
  }

  const removeAt = (index: number) => {
    const next = [...slots]
    next[index] = null
    onChange(next)
  }

  return (
    <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
      {slots.map((id, index) => {
        const pokemon = id ? teamMap.get(id) : undefined
        return (
          <div
            key={index}
            draggable={!!pokemon}
            onDragStart={() => setDragIndex(index)}
            onDragOver={(e) => e.preventDefault()}
            onDrop={() => handleDrop(index)}
            className="aspect-square border-2 border-dashed rounded-lg flex flex-col items-center justify-center p-2 relative bg-gray-50"
          >
            {pokemon ? (
              <div
                className="flex flex-col items-center w-full"
                title={
                  `Faible : ${pokemon.weaknesses.map((t) => TYPE_FR[t] ?? t).join(', ') || '—'}\n` +
                  `Résiste : ${pokemon.resistances.map((t) => TYPE_FR[t] ?? t).join(', ') || '—'}`
                }
              >
                <img
                  src={pokemon.sprite_url ?? undefined}
                  alt=""
                  width={48}
                  height={48}
                  style={{ imageRendering: 'pixelated' }}
                />
                <span className="text-xs text-center truncate w-full">
                  {pokemon.name_fr ?? pokemon.name_en}
                </span>
                {pokemon.weaknesses.length > 0 && (
                  <div className="flex gap-0.5 mt-0.5">
                    {pokemon.weaknesses.slice(0, 4).map((t) => (
                      <span
                        key={t}
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: TYPE_COLORS[t] ?? '#999' }}
                      />
                    ))}
                  </div>
                )}
                <button
                  onClick={() => removeAt(index)}
                  className="absolute top-1 right-1 text-gray-400 hover:text-red-500 text-xs"
                  aria-label={`Retirer ${pokemon.name_fr ?? pokemon.name_en}`}
                >
                  ×
                </button>
              </div>
            ) : (
              <span className="text-gray-300 text-2xl">+</span>
            )}
          </div>
        )
      })}
    </div>
  )
}
