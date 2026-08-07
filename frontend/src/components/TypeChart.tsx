import { useEffect, useState } from 'react'
import { fetchTypeChart, type TypeChartData } from '../api/analytics'
import { TYPE_COLORS, TYPE_FR } from '../constants/typeColors'

// Style de cellule par multiplicateur — les clés doivent matcher exactement
// les valeurs renvoyées par le chart (0, 0.5, 1, 2, 4 — jamais d'autre valeur
// possible puisque ce sont des produits de {0, 0.5, 1, 2}).
const CELL_STYLES: Record<string, string> = {
  '0': 'bg-gray-800 text-white',
  '0.5': 'bg-red-100 text-red-700',
  '1': 'bg-white text-gray-300',
  '2': 'bg-green-100 text-green-700',
  '4': 'bg-green-300 text-green-900',
}

function cellLabel(mult: number): string {
  if (mult === 1) return ''
  return `×${mult}`
}

function TypeHeader({ type }: { type: string }) {
  return (
    <div
      className="w-6 h-6 rounded flex items-center justify-center text-white text-[10px] font-bold"
      style={{ backgroundColor: TYPE_COLORS[type] ?? '#888' }}
      title={TYPE_FR[type] ?? type}
    >
      {(TYPE_FR[type] ?? type).slice(0, 1)}
    </div>
  )
}

export function TypeChart() {
  const [data, setData] = useState<TypeChartData | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchTypeChart()
      .then(setData)
      .catch(() => setError('Impossible de charger la matrice des types'))
  }, [])

  if (error) return <p className="text-sm text-red-500">{error}</p>
  if (!data) return <p className="text-sm text-gray-400 italic">Chargement…</p>

  return (
    <div className="overflow-x-auto">
      <p className="text-xs text-gray-400 mb-2">
        Attaquant en ligne, défenseur en colonne — ex. Feu (ligne) contre Plante
        (colonne) : ×2.
      </p>
      <table className="border-collapse text-xs">
        <thead>
          <tr>
            <th className="p-0.5" />
            {data.types.map((def) => (
              <th key={def} className="p-0.5">
                <TypeHeader type={def} />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.types.map((atk) => (
            <tr key={atk}>
              <th className="p-0.5">
                <TypeHeader type={atk} />
              </th>
              {data.types.map((def) => {
                const mult = data.matrix[atk][def]
                return (
                  <td
                    key={def}
                    className={`w-6 h-6 text-center border border-gray-100 ${
                      CELL_STYLES[String(mult)] ?? 'bg-white'
                    }`}
                    title={`${TYPE_FR[atk] ?? atk} → ${TYPE_FR[def] ?? def} : ×${mult}`}
                  >
                    {cellLabel(mult)}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
