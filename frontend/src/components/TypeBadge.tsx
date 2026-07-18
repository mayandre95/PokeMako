import { TYPE_COLORS, TYPE_FR } from '../constants/typeColors'

interface Props {
  type: string
}

export function TypeBadge({ type }: Props) {
  const color = TYPE_COLORS[type] ?? '#777'
  return (
    <span
      className="px-3 py-1 rounded-full text-white text-sm font-semibold"
      style={{ backgroundColor: color }}
    >
      {TYPE_FR[type] ?? type}
    </span>
  )
}
