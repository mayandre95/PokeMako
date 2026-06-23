const STAT_MAX = 255

const STAT_COLORS: Record<string, string> = {
  HP: '#FF5959',
  Attaque: '#F5AC78',
  Défense: '#FAE078',
  'Att. Spé': '#9DB7F5',
  'Déf. Spé': '#A7DB8D',
  Vitesse: '#FA92B2',
}

interface Props {
  label: string
  value: number | null
}

export function StatBar({ label, value }: Props) {
  const pct = Math.round(((value ?? 0) / STAT_MAX) * 100)
  const color = STAT_COLORS[label] ?? '#aaa'
  return (
    <div className="flex items-center gap-3">
      <span className="w-24 text-right text-sm text-gray-500 shrink-0">
        {label}
      </span>
      <span className="w-8 text-right text-sm font-semibold tabular-nums">
        {value ?? '—'}
      </span>
      <div className="flex-1 bg-gray-200 rounded-full h-2.5">
        <div
          className="h-2.5 rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  )
}
