interface Props {
  label: string
  value: number
  max: number
  color: string
  tooltip?: string
}

export function ScoreBar({ label, value, max, color, tooltip }: Props) {
  const pct = Math.min(100, Math.round((value / max) * 100))
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="flex items-center gap-1 text-gray-600">
          {label}
          {tooltip && (
            <span className="relative group cursor-default">
              <span className="text-gray-400 text-xs">ⓘ</span>
              <span className="absolute left-1/2 -translate-x-1/2 bottom-full mb-1.5 w-52 bg-gray-800 text-white text-xs rounded px-2 py-1.5 leading-snug opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                {tooltip}
                <span className="absolute left-1/2 -translate-x-1/2 top-full border-4 border-transparent border-t-gray-800" />
              </span>
            </span>
          )}
        </span>
        <span className="font-mono font-semibold text-gray-800">
          {Math.round(value)}
        </span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  )
}
