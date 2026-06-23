import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'
import { PokemonPage } from './pages/PokemonPage'

function HomePage() {
  const samples = [1, 4, 7, 25, 133, 150]
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center gap-6">
      <h1 className="text-4xl font-bold">PokéMako</h1>
      <p className="text-gray-500">Tester une fiche :</p>
      <div className="flex flex-wrap gap-3 justify-center">
        {samples.map((id) => (
          <Link
            key={id}
            to={`/pokemon/${id}`}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            #{id}
          </Link>
        ))}
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/pokemon/:id" element={<PokemonPage />} />
      </Routes>
    </BrowserRouter>
  )
}
