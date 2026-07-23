import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchMoveDetail, type MoveDetail } from '../api/pokemon'
import { TypeBadge } from '../components/TypeBadge'
import { DAMAGE_CLASS_FR, DAMAGE_CLASS_COLORS } from '../constants/methodNames'

export function MovePage() {
  const { id } = useParams<{ id: string }>()
  const [move, setMove] = useState<MoveDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    fetchMoveDetail(Number(id))
      .then((data) => {
        if (!data) setError('Attaque introuvable.')
        else setMove(data)
      })
      .catch(() => setError('Erreur de chargement.'))
      .finally(() => setLoading(false))
  }, [id])

  if (loading)
    return (
      <div className="flex justify-center items-center min-h-screen text-gray-500">
        Chargement…
      </div>
    )

  if (error || !move)
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <p className="text-red-500">{error ?? 'Attaque introuvable.'}</p>
        <Link to="/" className="text-blue-500 hover:underline">
          ← Accueil
        </Link>
      </div>
    )

  const name = move.name_fr ?? move.name_en

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-lg mx-auto mb-4">
        <button
          onClick={() => window.history.back()}
          className="text-blue-500 hover:underline text-sm"
        >
          ← Retour
        </button>
      </div>

      <div className="max-w-lg mx-auto bg-white rounded-2xl shadow-lg p-6">
        <h1 className="text-3xl font-bold mb-1">{name}</h1>
        <p className="text-gray-400 text-sm mb-4">
          #{String(move.id).padStart(4, '0')}
        </p>

        <div className="flex gap-2 mb-6">
          <TypeBadge type={move.type} />
          <span
            className="px-3 py-1 rounded-full text-white text-sm font-semibold"
            style={{
              backgroundColor: DAMAGE_CLASS_COLORS[move.damage_class] ?? '#888',
            }}
          >
            {DAMAGE_CLASS_FR[move.damage_class] ?? move.damage_class}
          </span>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-6 text-center">
          <div className="bg-gray-50 rounded-xl p-3">
            <p className="text-2xl font-bold">{move.power ?? '—'}</p>
            <p className="text-xs text-gray-500 mt-1">Puissance</p>
          </div>
          <div className="bg-gray-50 rounded-xl p-3">
            <p className="text-2xl font-bold">
              {move.accuracy != null ? `${move.accuracy} %` : '—'}
            </p>
            <p className="text-xs text-gray-500 mt-1">Précision</p>
          </div>
          <div className="bg-gray-50 rounded-xl p-3">
            <p className="text-2xl font-bold">{move.pp ?? '—'}</p>
            <p className="text-xs text-gray-500 mt-1">PP</p>
          </div>
        </div>

        {(move.effect_fr || move.effect_en) && (
          <div>
            <h2 className="font-semibold text-gray-700 mb-2">Effet</h2>
            <p className="text-gray-600 text-sm leading-relaxed">
              {move.effect_fr ?? move.effect_en}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
