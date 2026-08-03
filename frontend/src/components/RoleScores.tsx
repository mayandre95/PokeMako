import { ScoreBar } from './ScoreBar'
import { ROLE_LABELS, type RoleKey } from '../constants/roleLabels'

interface Props {
  scores: Record<RoleKey, number>
  dominantRole: RoleKey
}

export function RoleScores({ scores, dominantRole }: Props) {
  const dominant = ROLE_LABELS.find((r) => r.key === dominantRole)

  return (
    <div>
      {dominant && (
        <div className="mb-3">
          <span
            className="px-3 py-1 rounded-full text-white text-sm font-semibold"
            style={{ backgroundColor: dominant.color }}
          >
            Rôle dominant : {dominant.label}
          </span>
        </div>
      )}
      <div className="space-y-2">
        {ROLE_LABELS.map((role) => (
          <ScoreBar
            key={role.key}
            label={role.label}
            value={scores[role.key]}
            max={role.max}
            color={role.color}
            tooltip={role.tooltip}
          />
        ))}
      </div>
    </div>
  )
}
