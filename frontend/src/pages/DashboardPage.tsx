import { useEffect, useState } from 'react'
import Plot from 'react-plotly.js'
import { Link } from 'react-router-dom'
import {
  fetchTypeDistribution,
  fetchGenerationStats,
  fetchScatterData,
  type TypeDistribution,
  type GenerationStats,
  type ScatterPoint,
} from '../api/analytics'
import { TYPE_COLORS } from '../constants/typeColors'
import { STAT_LABELS } from '../constants/statLabels'

export default function DashboardPage() {
  const [types, setTypes] = useState<TypeDistribution[]>([])
  const [gens, setGens] = useState<GenerationStats[]>([])
  const [scatter, setScatter] = useState<ScatterPoint[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Les 3 appels en parallèle — un seul round-trip réseau
    Promise.all([
      fetchTypeDistribution(),
      fetchGenerationStats(),
      fetchScatterData(),
    ]).then(([t, g, s]) => {
      setTypes(t)
      setGens(g)
      setScatter(s)
      setLoading(false)
    })
  }, [])

  if (loading)
    return <div className="p-8 text-center text-gray-500">Chargement…</div>

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-10">
      <div className="max-w-2xl mx-auto mb-4">
        <Link to="/" className="text-blue-500 hover:underline text-sm">
          ← Retour
        </Link>
      </div>
      <h1 className="text-2xl font-bold">Dashboard Pokédex</h1>

      {/* Graphique 1 — Répartition des types */}
      <section>
        <h2 className="text-lg font-semibold mb-3">Répartition des 18 types</h2>
        <Plot
          data={[
            {
              type: 'bar',
              x: types.map((t) => t.type),
              y: types.map((t) => t.count),
              marker: {
                color: types.map((t) => TYPE_COLORS[t.type] ?? '#888'),
              },
              hovertemplate: '<b>%{x}</b><br>%{y} Pokémon<extra></extra>',
            },
          ]}
          layout={{
            autosize: true,
            xaxis: { title: 'Type' },
            yaxis: { title: 'Nombre de Pokémon' },
            margin: { t: 10, b: 80 },
          }}
          useResizeHandler
          style={{ width: '100%', height: 400 }}
        />
      </section>

      {/* Graphique 2 — Stats moyennes par génération */}
      <section>
        <h2 className="text-lg font-semibold mb-3">
          Stats moyennes par génération
        </h2>
        <Plot
          data={STAT_LABELS.map((stat) => ({
            type: 'scatter' as const,
            mode: 'lines+markers' as const,
            name: stat.label,
            x: gens.map((g) => `Gen ${g.generation}`),
            y: gens.map((g) => g[stat.key]),
            hovertemplate: `${stat.label}: <b>%{y:.1f}</b><extra></extra>`,
          }))}
          layout={{
            autosize: true,
            xaxis: { title: 'Génération' },
            yaxis: { title: 'Moyenne' },
            legend: { orientation: 'h', y: -0.2 },
            margin: { t: 10, b: 60 },
          }}
          useResizeHandler
          style={{ width: '100%', height: 420 }}
        />
      </section>

      {/* Graphique 3 — Scatter Vitesse vs Score de puissance */}
      <section>
        <h2 className="text-lg font-semibold mb-3">
          Vitesse vs Score de puissance
        </h2>
        <Plot
          data={[
            {
              type: 'scatter',
              mode: 'markers',
              x: scatter.map((p) => p.speed),
              y: scatter.map((p) => p.power_score),
              text: scatter.map((p) => p.name),
              marker: {
                color: scatter.map(
                  (p) => TYPE_COLORS[p.primary_type ?? ''] ?? '#888'
                ),
                size: 7,
                opacity: 0.7,
              },
              hovertemplate:
                '<b>%{text}</b><br>Vitesse : %{x}<br>Score de puissance : %{y}<extra></extra>',
            },
          ]}
          layout={{
            autosize: true,
            xaxis: { title: { text: 'Vitesse' } },
            yaxis: { title: { text: 'Score de puissance' } },
            margin: { t: 20, b: 60, l: 120 },
          }}
          config={{ displayModeBar: false }}
          useResizeHandler
          style={{ width: '100%', height: 450 }}
        />
      </section>
    </div>
  )
}
