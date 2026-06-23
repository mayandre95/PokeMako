import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchFlavorText, fetchPokemon, type Pokemon } from '../api/pokemon'
import { PokemonCard } from '../components/PokemonCard'

export function PokemonPage() {
  const { id } = useParams<{ id: string }>()
  const [pokemon, setPokemon] = useState<Pokemon | null>(null)
  const [flavorText, setFlavorText] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    setError(null)

    Promise.all([fetchPokemon(id), fetchFlavorText(Number(id))])
      .then(([poke, flavor]) => {
        setPokemon(poke)
        setFlavorText(flavor)
      })
      .catch((err) => setError((err as Error).message))
      .finally(() => setLoading(false))
  }, [id])

  if (loading)
    return (
      <div className="flex justify-center items-center min-h-screen text-gray-500">
        Chargement…
      </div>
    )

  if (error)
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <p className="text-red-500 font-medium">{error}</p>
        <Link to="/" className="text-blue-500 hover:underline">
          ← Retour
        </Link>
      </div>
    )

  if (!pokemon) return null

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto mb-4">
        <Link to="/" className="text-blue-500 hover:underline text-sm">
          ← Retour
        </Link>
      </div>
      <PokemonCard pokemon={pokemon} flavorText={flavorText} />
    </div>
  )
}
