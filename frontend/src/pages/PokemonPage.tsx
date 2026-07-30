import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  fetchEncounters,
  fetchEvolutionChain,
  fetchFlavorText,
  fetchMoves,
  fetchScores,
  fetchPokemon,
  type EncountersData,
  type EvolutionNode,
  type MovesData,
  type ScoresData,
  type Pokemon,
} from '../api/pokemon'
import { PokemonCard } from '../components/PokemonCard'

export function PokemonPage() {
  const { id } = useParams<{ id: string }>()
  const [pokemon, setPokemon] = useState<Pokemon | null>(null)
  const [encountersData, setEncountersData] = useState<EncountersData | null>(
    null
  )
  const [flavorText, setFlavorText] = useState('')
  const [evolutionTree, setEvolutionTree] = useState<EvolutionNode | null>(null)
  const [movesData, setMovesData] = useState<MovesData | null>(null)
  const [scoresData, setScoresData] = useState<ScoresData | null>(null)
  const [selectedGeneration, setSelectedGeneration] = useState<number | null>(
    null
  )
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    setError(null)
    setSelectedGeneration(null)

    Promise.all([
      fetchPokemon(id),
      fetchFlavorText(Number(id)),
      fetchEvolutionChain(Number(id)),
      fetchEncounters(Number(id)),
      fetchMoves(Number(id)),
      fetchScores(Number(id)),
    ])
      .then(([poke, flavor, evoChain, encounters, moves, scores]) => {
        setPokemon(poke)
        setFlavorText(flavor)
        setEvolutionTree(evoChain)
        setEncountersData(encounters)
        setMovesData(moves)
        setScoresData(scores)
      })
      .catch((err) => setError((err as Error).message))
      .finally(() => setLoading(false))
  }, [id])

  const handleGenerationChange = (gen: number | null) => {
    if (!id) return
    setSelectedGeneration(gen)
    fetchScores(Number(id), gen ?? undefined)
      .then(setScoresData)
      .catch(() => {})
  }

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
      <PokemonCard
        pokemon={pokemon}
        flavorText={flavorText}
        evolutionTree={evolutionTree}
        encountersData={encountersData}
        movesData={movesData}
        scoresData={scoresData}
        selectedGeneration={selectedGeneration}
        onGenerationChange={handleGenerationChange}
      />
    </div>
  )
}
