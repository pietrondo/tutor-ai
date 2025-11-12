'use client'

import { useEffect, useMemo, useState } from 'react'
import { Search as SearchIcon, SlidersHorizontal, Sparkles, Filter, BookOpen, Tag, Clock3, UserCircle, Compass, Database, RefreshCcw } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { cn, formatDateTime, truncateText } from '@/lib/utils'
import type { AdvancedSearchResponse, SearchFacets, SearchResult, SearchType, SortOrder } from '@/types/search'

interface CourseSummary {
  id: string
  name: string
  subject?: string
}

interface BookSummary {
  id: string
  title: string
}

const searchTypeOptions: Array<{ value: SearchType; label: string; description: string }> = [
  { value: 'text', label: 'Ricerca Testuale', description: 'Ricerca basata su parole chiave nei contenuti indicizzati' },
  { value: 'semantic', label: 'Ricerca Semantica', description: 'Comprende il significato delle frasi (beta)' },
  { value: 'hybrid', label: 'Ricerca Ibrida', description: 'Combina matching esatto e semantico' }
]

const sortOptions: Array<{ value: SortOrder; label: string }> = [
  { value: 'relevance', label: 'Rilevanza' },
  { value: 'date', label: 'Data' },
  { value: 'alphabetical', label: 'Alfabetico' },
  { value: 'confidence', label: 'Confidenza' }
]

const annotationTypeOptions: Array<{ value: string; label: string }> = [
  { value: 'highlight', label: 'Evidenziazione' },
  { value: 'underline', label: 'Sottolineatura' },
  { value: 'note', label: 'Nota' },
  { value: 'strikeout', label: 'Barrato' },
  { value: 'text', label: 'Testo' }
]

export default function AdvancedSearchPage() {
  const [query, setQuery] = useState('')
  const [searchType, setSearchType] = useState<SearchType>('text')
  const [sortOrder, setSortOrder] = useState<SortOrder>('relevance')
  const [courses, setCourses] = useState<CourseSummary[]>([])
  const [booksByCourse, setBooksByCourse] = useState<Record<string, BookSummary[]>>({})
  const [selectedCourse, setSelectedCourse] = useState<string>('all')
  const [selectedBook, setSelectedBook] = useState<string>('all')
  const [selectedAnnotationTypes, setSelectedAnnotationTypes] = useState<string[]>([])
  const [onlyFavorites, setOnlyFavorites] = useState(false)
  const [onlyPublic, setOnlyPublic] = useState(false)
  const [minTextLength, setMinTextLength] = useState<string>('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [facets, setFacets] = useState<SearchFacets | undefined>(undefined)
  const [totalCount, setTotalCount] = useState(0)
  const [searchTime, setSearchTime] = useState<number | null>(null)
  const [hasMore, setHasMore] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)

  useEffect(() => {
    const loadCourses = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/courses`)
        if (!response.ok) return

        const payload = await response.json()
        const courseList = Array.isArray(payload.courses)
          ? payload.courses
              .filter((course: unknown): course is CourseSummary => Boolean(course && (course as CourseSummary).id))
              .map((course: CourseSummary) => ({
                id: course.id,
                name: course.name,
                subject: course.subject
              }))
          : []
        setCourses(courseList)
      } catch (fetchError) {
        console.error('Errore nel caricamento dei corsi:', fetchError)
      }
    }

    loadCourses()
  }, [])

  useEffect(() => {
    if (query.trim().length < 3) {
      setSuggestions([])
      setShowSuggestions(false)
      return
    }

    const timeoutId = setTimeout(async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/search/suggestions?q=${encodeURIComponent(query)}&limit=8`)
        if (!response.ok) return
        const data = await response.json()
        if (Array.isArray(data.suggestions)) {
          setSuggestions(data.suggestions)
          setShowSuggestions(true)
        } else {
          setSuggestions([])
          setShowSuggestions(false)
        }
      } catch (fetchError) {
        console.error('Errore nel recupero dei suggerimenti:', fetchError)
      }
    }, 300)

    return () => clearTimeout(timeoutId)
  }, [query])

  useEffect(() => {
    if (selectedCourse === 'all' || booksByCourse[selectedCourse]) {
      return
    }

    const loadBooks = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/courses/${selectedCourse}/books`)
        if (!response.ok) return

        const payload = await response.json()
        if (Array.isArray(payload.books)) {
          setBooksByCourse((prev) => ({
            ...prev,
            [selectedCourse]: payload.books
              .filter((book: unknown): book is BookSummary => Boolean(book && (book as BookSummary).id))
              .map((book: BookSummary) => ({ id: book.id, title: book.title }))
          }))
        }
      } catch (fetchError) {
        console.error('Errore nel caricamento dei libri:', fetchError)
      }
    }

    loadBooks()
  }, [selectedCourse, booksByCourse])

  const availableBooks = useMemo(() => {
    if (selectedCourse === 'all') return []
    return booksByCourse[selectedCourse] ?? []
  }, [booksByCourse, selectedCourse])

  const handleToggleAnnotationType = (value: string) => {
    setSelectedAnnotationTypes((prev) =>
      prev.includes(value) ? prev.filter((item) => item !== value) : [...prev, value]
    )
  }

  const buildFilters = () => {
    const filters: Record<string, unknown> = {}

    if (selectedCourse !== 'all') {
      filters.course_ids = [selectedCourse]
    }
    if (selectedBook !== 'all') {
      filters.book_ids = [selectedBook]
    }
    if (selectedAnnotationTypes.length > 0) {
      filters.annotation_types = selectedAnnotationTypes
    }
    if (onlyFavorites) {
      filters.is_favorite = true
    }
    if (onlyPublic) {
      filters.is_public = true
    }
    if (minTextLength) {
      const parsed = parseInt(minTextLength, 10)
      if (!Number.isNaN(parsed)) {
        filters.min_text_length = parsed
      }
    }

    return filters
  }

  const handleSearch = async (overrideQuery?: string) => {
    const queryToUse = (overrideQuery ?? query).trim()
    if (!queryToUse) {
      setError('Inserisci una query di ricerca per iniziare.')
      setResults([])
      setFacets(undefined)
      setHasSearched(false)
      return
    }

    setLoading(true)
    setError(null)
    setHasSearched(true)

    try {
      const filters = buildFilters()
      const payload = {
        query: queryToUse,
        search_type: searchType,
        sort_order: sortOrder,
        limit: 20,
        offset: 0,
        include_highlights: true,
        highlight_tags: true,
        ...(Object.keys(filters).length > 0 ? { filters } : {})
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/search/advanced`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        throw new Error('Ricerca fallita, riprova tra poco')
      }

      const data: AdvancedSearchResponse = await response.json()
      setResults(Array.isArray(data.results) ? data.results : [])
      setFacets(data.facets)
      setTotalCount(data.total_count ?? 0)
      setHasMore(Boolean(data.has_more))
      setSearchTime(typeof data.search_time === 'number' ? data.search_time : null)
      setShowSuggestions(false)
    } catch (searchError) {
      console.error('Errore durante la ricerca:', searchError)
      setError(searchError instanceof Error ? searchError.message : 'Errore inatteso durante la ricerca')
    } finally {
      setLoading(false)
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion)
    setShowSuggestions(false)
    void handleSearch(suggestion)
  }

  const renderHighlights = (highlight: string) => {
    const parts = highlight.split('**')
    return parts.map((part, index) => {
      const isHighlight = index % 2 === 1
      if (!part) {
        return null
      }
      return isHighlight ? (
        <mark key={`${part}-${index}`} className="rounded bg-yellow-200 px-0.5 text-yellow-900">
          {part}
        </mark>
      ) : (
        <span key={`${part}-${index}`}>{part}</span>
      )
    })
  }

  const getCourseName = (courseId: string) => {
    const course = courses.find((item) => item.id === courseId)
    return course ? course.name : courseId
  }

  const getBookTitle = (courseId: string, bookId: string) => {
    const courseBooks = booksByCourse[courseId]
    if (!courseBooks) return bookId
    const book = courseBooks.find((item) => item.id === bookId)
    return book ? book.title : bookId
  }

  return (
    <div className="space-y-10">
      <header className="glass rounded-3xl border border-white/60 bg-white/70 p-8 shadow-xl shadow-blue-100/40 dark:bg-gray-900/60 dark:border-gray-800/80">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <div className="rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 p-3 text-white shadow-lg shadow-blue-500/40">
                <SearchIcon className="h-6 w-6" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Ricerca Avanzata Contenuti</h1>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                  Esplora annotazioni, risultati OCR e contenuti indicizzati con filtri personalizzati e suggerimenti intelligenti.
                </p>
              </div>
            </div>
            {searchTime !== null && (
              <p className="mt-4 flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                <Clock3 className="h-4 w-4" />
                Risultati ottenuti in {searchTime.toFixed(2)} secondi • {totalCount} risultati totali {hasMore ? '(altri disponibili)' : ''}
              </p>
            )}
          </div>
          <div className="flex flex-col items-start gap-2 rounded-2xl border border-blue-100 bg-blue-50/70 p-4 text-blue-700 dark:bg-blue-500/10 dark:text-blue-200">
            <div className="flex items-center gap-2 font-semibold">
              <Sparkles className="h-5 w-5" />
              Suggerimento
            </div>
            <p className="text-sm leading-5">
              Combina filtri e ricerca semantica per risultati più pertinenti. Attiva l&apos;opzione &quot;Ricerca Ibrida&quot; per sfruttare il meglio di entrambi i mondi.
            </p>
          </div>
        </div>
      </header>

      <section className="glass rounded-3xl border border-white/60 bg-white/80 p-6 shadow-lg shadow-blue-100/30 dark:bg-gray-900/60 dark:border-gray-800/70">
        <div className="space-y-6">
          <div className="relative">
            <label htmlFor="search-query" className="mb-2 block text-sm font-semibold text-slate-700 dark:text-slate-200">
              Query di ricerca
            </label>
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
              <div className="relative flex-1">
                <SearchIcon className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
                <input
                  id="search-query"
                  type="text"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  onFocus={() => setShowSuggestions(suggestions.length > 0)}
                  onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
                  placeholder="Cerca concetti, annotazioni, termini chiave..."
                  className="w-full rounded-2xl border border-slate-200/80 bg-white py-4 pl-12 pr-4 text-slate-900 shadow-inner focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-100 dark:bg-gray-900 dark:text-white dark:border-gray-700 dark:focus:ring-blue-500/40"
                />
                {showSuggestions && suggestions.length > 0 && (
                  <div className="absolute z-20 mt-2 w-full rounded-2xl border border-slate-200 bg-white p-2 shadow-xl dark:border-gray-700 dark:bg-gray-900">
                    <p className="px-3 pb-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                      Suggerimenti
                    </p>
                    <div className="space-y-1">
                      {suggestions.map((suggestion) => (
                        <button
                          key={suggestion}
                          type="button"
                          onMouseDown={(event) => event.preventDefault()}
                          onClick={() => handleSuggestionClick(suggestion)}
                          className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-sm text-slate-700 transition-colors hover:bg-blue-50 dark:text-slate-200 dark:hover:bg-blue-500/20"
                        >
                          <Sparkles className="h-4 w-4 text-blue-500" />
                          <span>{suggestion}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <Button
                type="button"
                variant="accent"
                size="lg"
                icon={<SearchIcon />}
                onClick={() => void handleSearch()}
                loading={loading}
                className="w-full rounded-2xl lg:w-auto"
              >
                Avvia ricerca
              </Button>
            </div>
            {error && (
              <p className="mt-2 text-sm text-red-600 dark:text-red-400">
                {error}
              </p>
            )}
          </div>

          <div className="grid gap-6 lg:grid-cols-12">
            <div className="lg:col-span-5 space-y-6">
              <div>
                <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">
                  <SlidersHorizontal className="h-4 w-4" />
                  Modalità di ricerca
                </h3>
                <div className="grid gap-3">
                  {searchTypeOptions.map((option) => {
                    const isActive = option.value === searchType
                    return (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => setSearchType(option.value)}
                        className={cn(
                          'flex w-full items-start gap-3 rounded-2xl border p-4 text-left transition-all',
                          isActive
                            ? 'border-blue-500 bg-blue-50/80 shadow-lg shadow-blue-200/40 dark:bg-blue-500/20 dark:border-blue-400'
                            : 'border-slate-200 hover:border-blue-400 hover:bg-blue-50/40 dark:border-gray-700 dark:hover:bg-blue-500/10'
                        )}
                      >
                        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-300">
                          <Compass className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">{option.label}</p>
                          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{option.description}</p>
                        </div>
                      </button>
                    )
                  })}
                </div>
              </div>

              <div>
                <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">
                  <Filter className="h-4 w-4" />
                  Filtri principali
                </h3>
                <div className="grid gap-4">
                  <div>
                    <label className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-300">Corso</label>
                    <select
                      value={selectedCourse}
                      onChange={(event) => {
                        const value = event.target.value
                        setSelectedCourse(value)
                        setSelectedBook('all')
                      }}
                      className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 shadow-inner focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-100 dark:bg-gray-900 dark:text-white dark:border-gray-700 dark:focus:ring-blue-500/30"
                    >
                      <option value="all">Tutti i corsi</option>
                      {courses.map((course) => (
                        <option key={course.id} value={course.id}>
                          {course.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-300">Libro / materiale</label>
                    <select
                      value={selectedBook}
                      onChange={(event) => setSelectedBook(event.target.value)}
                      disabled={selectedCourse === 'all'}
                      className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 shadow-inner disabled:opacity-60 focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-100 dark:bg-gray-900 dark:text-white dark:border-gray-700 dark:focus:ring-blue-500/30"
                    >
                      <option value="all">Tutti i materiali</option>
                      {availableBooks.map((book) => (
                        <option key={book.id} value={book.id}>
                          {book.title}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-300">Tipo annotazione</label>
                    <div className="mt-2 grid gap-2 sm:grid-cols-2">
                      {annotationTypeOptions.map((option) => {
                        const isActive = selectedAnnotationTypes.includes(option.value)
                        return (
                          <button
                            key={option.value}
                            type="button"
                            onClick={() => handleToggleAnnotationType(option.value)}
                            className={cn(
                              'flex items-center gap-2 rounded-xl border px-3 py-2 text-sm transition-all',
                              isActive
                                ? 'border-purple-500 bg-purple-50/80 text-purple-700 shadow-inner dark:bg-purple-500/20 dark:text-purple-200 dark:border-purple-400'
                                : 'border-slate-200 text-slate-600 hover:border-purple-400 hover:bg-purple-50/40 dark:border-gray-700 dark:text-slate-300 dark:hover:bg-purple-500/10'
                            )}
                          >
                            <Tag className="h-4 w-4" />
                            {option.label}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="lg:col-span-7 space-y-6">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-300">Ordinamento</label>
                  <select
                    value={sortOrder}
                    onChange={(event) => setSortOrder(event.target.value as SortOrder)}
                    className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 shadow-inner focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-100 dark:bg-gray-900 dark:text-white dark:border-gray-700 dark:focus:ring-blue-500/30"
                  >
                    {sortOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-300">Lunghezza minima testo</label>
                  <input
                    type="number"
                    min={0}
                    placeholder="Es. 50 caratteri"
                    value={minTextLength}
                    onChange={(event) => setMinTextLength(event.target.value)}
                    className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 shadow-inner focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-100 dark:bg-gray-900 dark:text-white dark:border-gray-700 dark:focus:ring-blue-500/30"
                  />
                </div>
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-inner transition-all hover:border-blue-400 hover:bg-blue-50/40 dark:border-gray-700 dark:bg-gray-900 dark:text-slate-200 dark:hover:bg-blue-500/10">
                  <input
                    type="checkbox"
                    checked={onlyFavorites}
                    onChange={(event) => setOnlyFavorites(event.target.checked)}
                    className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  Mostra solo preferiti
                </label>

                <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-inner transition-all hover:border-blue-400 hover:bg-blue-50/40 dark:border-gray-700 dark:bg-gray-900 dark:text-slate-200 dark:hover:bg-blue-500/10">
                  <input
                    type="checkbox"
                    checked={onlyPublic}
                    onChange={(event) => setOnlyPublic(event.target.checked)}
                    className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  Mostra solo annotazioni pubbliche
                </label>
              </div>

              <div className="rounded-2xl border border-slate-200/80 bg-slate-50/60 p-4 text-sm text-slate-600 dark:border-gray-700 dark:bg-gray-800/70 dark:text-slate-300">
                <p className="flex items-center gap-2 font-medium text-slate-700 dark:text-slate-200">
                  <Database className="h-4 w-4 text-blue-500" />
                  Suggerimento avanzato
                </p>
                <p className="mt-1 leading-relaxed">
                  I filtri si applicano principalmente alle annotazioni. I risultati OCR e contenuti PDF potrebbero non supportare tutte le opzioni disponibili.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-2xl font-semibold text-slate-900 dark:text-white">Risultati</h2>
          <div className="flex items-center gap-3 text-sm text-slate-500 dark:text-slate-300">
            {loading && (
              <span className="flex items-center gap-2 text-blue-600 dark:text-blue-300">
                <RefreshCcw className="h-4 w-4 animate-spin" />
                Ricerca in corso...
              </span>
            )}
            {!loading && hasSearched && (
              <span>
                {totalCount} risultati • ordinati per <strong>{sortOptions.find((opt) => opt.value === sortOrder)?.label ?? 'rilevanza'}</strong>
              </span>
            )}
          </div>
        </div>

        {facets && Object.keys(facets).length > 0 && (
          <div className="mb-6 grid gap-4 md:grid-cols-3">
            {Object.entries(facets).map(([facetName, facetValues]) => (
              <div
                key={facetName}
                className="rounded-2xl border border-slate-200/70 bg-white/80 p-4 shadow-inner dark:border-gray-700 dark:bg-gray-900/60"
              >
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">
                  {facetName}
                </p>
                <ul className="mt-3 space-y-1 text-sm text-slate-600 dark:text-slate-300">
                  {Object.entries(facetValues).map(([label, count]) => (
                    <li key={label} className="flex items-center justify-between">
                      <span className="truncate pr-2">{label || '—'}</span>
                      <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700 dark:bg-gray-800 dark:text-slate-200">
                        {count}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}

        {!loading && hasSearched && results.length === 0 && (
          <div className="rounded-3xl border border-dashed border-slate-300 bg-white/70 p-12 text-center dark:border-gray-700 dark:bg-gray-900/50">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-500/10 text-blue-600">
              <SearchIcon className="h-6 w-6" />
            </div>
            <h3 className="mt-4 text-xl font-semibold text-slate-800 dark:text-slate-100">Nessun risultato trovato</h3>
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-300">
              Prova ad ampliare la ricerca, rimuovere alcuni filtri oppure utilizza sinonimi per ottenere risultati differenti.
            </p>
          </div>
        )}

        <div className="grid gap-4">
          {results.map((result) => {
            const highlights = result.metadata?.highlights ?? []
            const matchedTerms = Array.isArray(result.metadata?.matched_terms) ? result.metadata?.matched_terms : []
            const annotationType = typeof result.metadata?.annotation_type === 'string' ? result.metadata?.annotation_type : undefined

            return (
              <article
                key={`${result.type}-${result.id}`}
                className="rounded-3xl border border-white/60 bg-white/90 p-6 shadow-lg shadow-blue-100/30 transition-all hover:shadow-2xl dark:border-gray-800/70 dark:bg-gray-900/70"
              >
                <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                  <div className="space-y-3">
                    <div className="flex flex-wrap items-center gap-3">
                      <span className={cn(
                        'inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide',
                        result.type === 'annotation'
                          ? 'bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-200'
                          : result.type === 'ocr_result'
                            ? 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-200'
                            : 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-200'
                      )}>
                        {result.type === 'annotation' ? <Tag className="h-3.5 w-3.5" /> : <BookOpen className="h-3.5 w-3.5" />}
                        {result.type.replace(/_/g, ' ')}
                      </span>
                      {annotationType && (
                        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600 dark:bg-gray-800 dark:text-slate-300">
                          {annotationType}
                        </span>
                      )}
                      <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600 dark:bg-gray-800 dark:text-slate-300">
                        Score {result.score.toFixed(1)}
                      </span>
                      {typeof result.confidence === 'number' && (
                        <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-200">
                          Confidenza {Math.round(result.confidence)}%
                        </span>
                      )}
                    </div>

                    <div>
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{result.title || 'Risultato senza titolo'}</h3>
                      {matchedTerms.length > 0 && (
                        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                          Termini rilevati: {matchedTerms.join(', ')}
                        </p>
                      )}
                    </div>

                    <div className="space-y-2 text-sm text-slate-600 dark:text-slate-300">
                      {highlights.length > 0 ? (
                        highlights.map((highlight, index) => (
                          <p key={`${result.id}-highlight-${index}`} className="leading-relaxed">
                            {renderHighlights(highlight)}
                          </p>
                        ))
                      ) : (
                        <p className="leading-relaxed">
                          {truncateText(result.content ?? '', 220)}
                        </p>
                      )}
                    </div>

                    {Array.isArray(result.tags) && result.tags.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {result.tags.map((tag) => (
                          <span key={tag} className="rounded-full bg-blue-100/80 px-3 py-1 text-xs text-blue-700 dark:bg-blue-500/20 dark:text-blue-200">
                            #{tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="flex flex-col items-start gap-2 text-xs text-slate-500 dark:text-slate-400">
                    <div className="rounded-2xl border border-slate-200/70 bg-slate-50/70 px-4 py-3 dark:border-gray-800 dark:bg-gray-800/80">
                      <p className="flex items-center gap-2">
                        <BookOpen className="h-4 w-4 text-blue-500" />
                        <span className="font-medium text-slate-700 dark:text-slate-200">
                          {getCourseName(result.course_id)}
                        </span>
                      </p>
                      {result.book_id && (
                        <p className="mt-1 flex items-center gap-2">
                          <Tag className="h-4 w-4 text-purple-500" />
                          <span>{getBookTitle(result.course_id, result.book_id)}</span>
                        </p>
                      )}
                      {result.page_number && (
                        <p className="mt-1">Pagina {result.page_number}</p>
                      )}
                      {result.user_id && (
                        <p className="mt-1 flex items-center gap-2">
                          <UserCircle className="h-4 w-4 text-slate-400" />
                          <span>{result.user_id}</span>
                        </p>
                      )}
                      <p className="mt-1 text-[11px] text-slate-400">
                        Sorgente: {result.source}
                      </p>
                    </div>
                    {result.created_at && (
                      <p className="flex items-center gap-2 text-xs text-slate-400 dark:text-slate-500">
                        <Clock3 className="h-4 w-4" />
                        {formatDateTime(result.created_at)}
                      </p>
                    )}
                  </div>
                </div>
              </article>
            )
          })}
        </div>
      </section>
    </div>
  )
}
