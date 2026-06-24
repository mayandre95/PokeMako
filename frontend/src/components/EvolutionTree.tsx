import { Link } from 'react-router-dom'
import type { EvolutionCondition, EvolutionNode } from '../api/pokemon'

function formatName(name: string): string {
  return name
    .split('-')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

function conditionLabel(c: EvolutionCondition): string {
  if (c.trigger === 'trade') {
    return c.held_item ? `Échange\n(${formatName(c.held_item)})` : 'Échange'
  }
  if (c.trigger === 'use-item' && c.item) return formatName(c.item)
  if (c.min_level) {
    let label = `Niv. ${c.min_level}`
    if (c.time_of_day === 'day') label += '\n(jour)'
    else if (c.time_of_day === 'night') label += '\n(nuit)'
    else if (c.time_of_day === 'dusk') label += '\n(zénith)'
    return label
  }
  if (c.min_happiness) {
    let label = 'Bonheur'
    if (c.time_of_day === 'day') label += '\n(jour)'
    else if (c.time_of_day === 'night') label += '\n(nuit)'
    return label
  }
  if (c.known_move_type) return `Attaque\n${formatName(c.known_move_type)}`
  if (c.location) return formatName(c.location)
  return formatName(c.trigger)
}

function NodeCard({
  node,
  isCurrent,
}: {
  node: EvolutionNode
  isCurrent: boolean
}) {
  return (
    <Link
      to={`/pokemon/${node.id}`}
      className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors ${
        isCurrent ? 'bg-blue-50 ring-2 ring-blue-400' : 'hover:bg-gray-100'
      }`}
    >
      <img
        src={node.sprite_url}
        alt={node.name}
        width={64}
        height={64}
        style={{ imageRendering: 'pixelated' }}
      />
      <span className="text-xs font-medium capitalize text-gray-700">
        {node.name}
      </span>
      <span className="text-xs text-gray-400">
        #{String(node.id).padStart(4, '0')}
      </span>
    </Link>
  )
}

function Arrow({ conditions }: { conditions: EvolutionCondition[] }) {
  const label = conditions.map(conditionLabel).join('\nou ')
  return (
    <div className="flex flex-col items-center mx-1 text-gray-500 min-w-[48px]">
      <span className="text-xs text-center whitespace-pre-line leading-tight">
        {label}
      </span>
      <span className="text-lg">→</span>
    </div>
  )
}

function Branch({
  node,
  currentId,
}: {
  node: EvolutionNode
  currentId: number
}) {
  return (
    <div className="flex items-center">
      <NodeCard node={node} isCurrent={node.id === currentId} />
      {node.evolves_to.length > 0 && (
        <div className="flex flex-col gap-2">
          {node.evolves_to.map((child) => (
            <div key={child.id} className="flex items-center">
              {child.conditions.length > 0 && (
                <Arrow conditions={child.conditions} />
              )}
              <Branch node={child} currentId={currentId} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

interface Props {
  root: EvolutionNode
  currentId: number
}

export function EvolutionTree({ root, currentId }: Props) {
  return (
    <div className="overflow-x-auto">
      <div className="flex items-center min-w-max py-2 px-2">
        <Branch node={root} currentId={currentId} />
      </div>
    </div>
  )
}
