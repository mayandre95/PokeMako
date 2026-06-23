import { TYPE_COLORS } from '../constants/typeColors'

interface Props {
  type: string
}

export function TypeBadge({ type }: Props) {
  const color = TYPE_COLORS[type] ?? '#777'
  return (
    <span
      className="px-3 py-1 rounded-full text-white text-sm font-semibold capitalize"
      style={{ backgroundColor: color }}
    >
      {type}
    </span>
  )
}
