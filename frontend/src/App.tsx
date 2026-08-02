import {
  BrowserRouter,
  Link,
  Route,
  Routes,
  useNavigate,
} from 'react-router-dom'
import { PokemonPage } from './pages/PokemonPage'
import { MovePage } from './pages/MovePage'
import { lazy, Suspense } from 'react'
import { PokemonSearchBar } from './components/PokemonSearchBar'

const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const ComparePage = lazy(() => import('./pages/ComparePage'))

function HomePage() {
  const samples = [1, 4, 7, 25, 133, 150]
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center gap-6">
      <h1 className="text-4xl font-bold">PokéMako</h1>

      <div className="w-full max-w-sm">
        <PokemonSearchBar onSelect={(id) => navigate(`/pokemon/${id}`)} />
      </div>

      <p className="text-gray-500">Consulter une fiche Pokémon :</p>
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
      <div className="flex gap-3">
        <Link
          to="/dashboard"
          className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          Dashboard
        </Link>
        <Link
          to="/compare"
          className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
        >
          Comparateur
        </Link>
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
        <Route path="/move/:id" element={<MovePage />} />
        <Route
          path="/dashboard"
          element={
            <Suspense
              fallback={<div className="p-8 text-center">Chargement…</div>}
            >
              <DashboardPage />
            </Suspense>
          }
        />
        <Route
          path="/compare"
          element={
            <Suspense
              fallback={<div className="p-8 text-center">Chargement…</div>}
            >
              <ComparePage />
            </Suspense>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}
