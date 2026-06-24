import { Link } from 'react-router-dom'
import type { EvolutionCondition, EvolutionNode } from '../api/pokemon'
import { ITEM_FR } from '../constants/itemNames'
import { TYPE_FR } from '../constants/typeColors'

function formatName(name: string): string {
  return name
    .split('-')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

function itemName(name: string): string {
  return ITEM_FR[name] ?? formatName(name)
}

function typeName(name: string): string {
  return TYPE_FR[name] ?? formatName(name)
}

function conditionLabel(c: EvolutionCondition): string {
  // Échange et Pierre sont des triggers exclusifs, jamais combinés.
  if (c.trigger === 'trade') {
    return c.held_item ? `Échange\n(${itemName(c.held_item)})` : 'Échange'
  }
  if (c.trigger === 'use-item' && c.item) return itemName(c.item)

  // Pour les autres triggers, plusieurs conditions peuvent coexister
  // dans la même entrée (ex : Nymphali = Attaque Fée + Bonheur).
  const parts: string[] = []

  if (c.min_level) {
    let label = `Niv. ${c.min_level}`
    if (c.time_of_day === 'day') label += ' (jour)'
    else if (c.time_of_day === 'night') label += ' (nuit)'
    else if (c.time_of_day === 'dusk') label += ' (zénith)'
    parts.push(label)
  }

  if (c.known_move_type) parts.push(`Attaque ${typeName(c.known_move_type)}`)

  if (c.min_happiness) parts.push('Bonheur')

  if (parts.length > 0) return parts.join('\n+ ')

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

function Arrow({ condition }: { condition: EvolutionCondition }) {
  return (
    <div className="flex flex-col items-center mx-1 text-gray-500 min-w-[48px]">
      <span className="text-xs text-center whitespace-pre-line leading-tight">
        {conditionLabel(condition)}
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
  // Chaque condition d'un enfant devient une branche visuelle distincte.
  // Les conditions produisant le même label sont dédupliquées (ex : même pierre
  // référencée dans plusieurs générations).
  type ExpandedChild = {
    child: EvolutionNode
    condition: EvolutionCondition | null
    key: string
  }
  const expandedChildren = node.evolves_to.flatMap((child): ExpandedChild[] => {
    const seen = new Set<string>()
    const allLabels = child.conditions.map(conditionLabel)
    const unique = child.conditions.filter((c, i) => {
      const label = allLabels[i]
      // Supprimer si un autre label étend celui-ci (ex : "Attaque Fée" ⊂ "Attaque Fée\n+ Bonheur")
      if (
        allLabels.some((other, j) => j !== i && other.startsWith(label + '\n+'))
      )
        return false
      if (seen.has(label)) return false
      seen.add(label)
      return true
    })
    if (unique.length === 0) {
      return [{ child, condition: null, key: String(child.id) }]
    }
    return unique.map((c, i) => ({
      child,
      condition: c,
      key: `${child.id}-${i}`,
    }))
  })

  return (
    <div className="flex items-center">
      <NodeCard node={node} isCurrent={node.id === currentId} />
      {expandedChildren.length > 0 && (
        <div className="flex flex-col gap-2">
          {expandedChildren.map(({ child, condition, key }) => (
            <div key={key} className="flex items-center">
              {condition && <Arrow condition={condition} />}
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
