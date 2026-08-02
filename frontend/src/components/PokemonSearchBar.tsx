import { useEffect, useRef, useState } from 'react'
import { fetchSearch, type SearchResult } from '../api/search'

interface Props {
  onSelect: (id: number) => void
  placeholder?: string
  disabled?: boolean
}

export function PokemonSearchBar({
  onSelect,
  placeholder = 'Rechercher un Pokémon…',
  disabled = false,
}: Props) {
  const [query, setQuery] = useState('')
  const [suggestions, setSuggestions] = useState<SearchResult[]>([])
  const [showSugg, setShowSugg] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (query.length < 2) {
      setSuggestions([])
      return
    }
    const timer = setTimeout(
      () => fetchSearch(query).then(setSuggestions).catch(console.error),
      300
    )
    return () => clearTimeout(timer)
  }, [query])

  const handleSelect = (id: number) => {
    onSelect(id)
    setQuery('')
    setSuggestions([])
  }

  return (
    <div className="relative">
      <input
        ref={inputRef}
        value={query}
        onChange={(e) => {
          setQuery(e.target.value)
          setShowSugg(true)
        }}
        onFocus={() => setShowSugg(true)}
        onBlur={() => setTimeout(() => setShowSugg(false), 150)}
        placeholder={placeholder}
        disabled={disabled}
        className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:opacity-50"
      />
      {showSugg && suggestions.length > 0 && (
        <ul className="absolute z-10 w-full bg-white border rounded-lg shadow-lg mt-1 max-h-60 overflow-y-auto">
          {suggestions.map((s) => (
            <li
              key={s.id}
              onMouseDown={() => handleSelect(s.id)}
              className="flex items-center gap-2 px-3 py-2 hover:bg-gray-100 cursor-pointer"
            >
              {s.sprite_url && (
                <img
                  src={s.sprite_url}
                  alt=""
                  width={32}
                  height={32}
                  style={{ imageRendering: 'pixelated' }}
                />
              )}
              <span className="font-medium">{s.name_fr ?? s.name_en}</span>
              <span className="text-gray-400 text-xs ml-auto">#{s.id}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
