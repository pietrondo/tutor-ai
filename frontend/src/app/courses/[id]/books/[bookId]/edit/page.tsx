'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Save, X, Plus } from 'lucide-react'

interface Book {
  id: string
  title: string
  author: string
  isbn: string
  description: string
  year: string
  publisher: string
  chapters: string[]
  tags: string[]
}

export default function EditBookPage() {
  const params = useParams()
  const router = useRouter()
  const courseId = params.id as string
  const bookId = params.bookId as string

  const [book, setBook] = useState<Book | null>(null)
  const [courseName, setCourseName] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    author: '',
    isbn: '',
    description: '',
    year: '',
    publisher: '',
    chapters: [] as string[],
    tags: [] as string[]
  })

  const [newChapter, setNewChapter] = useState('')
  const [newTag, setNewTag] = useState('')

  useEffect(() => {
    fetchBook()
    fetchCourseInfo()
  }, [courseId, bookId])

  const fetchBook = async () => {
    try {
      const response = await fetch(`/api/courses/${courseId}/books/${bookId}`)
      if (response.ok) {
        const data = await response.json()
        setBook(data.book)
        setFormData({
          title: data.book.title || '',
          author: data.book.author || '',
          isbn: data.book.isbn || '',
          description: data.book.description || '',
          year: data.book.year || '',
          publisher: data.book.publisher || '',
          chapters: data.book.chapters || [],
          tags: data.book.tags || []
        })
      } else {
        setError('Errore nel caricamento del libro')
      }
    } catch (error) {
      setError('Errore nel caricamento del libro')
    } finally {
      setLoading(false)
    }
  }

  const fetchCourseInfo = async () => {
    try {
      const response = await fetch(`/api/courses/${courseId}`)
      if (response.ok) {
        const data = await response.json()
        setCourseName(data.course.name)
      }
    } catch (error) {
      console.error('Error fetching course info:', error)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const addChapter = () => {
    if (newChapter.trim()) {
      setFormData(prev => ({
        ...prev,
        chapters: [...prev.chapters, newChapter.trim()]
      }))
      setNewChapter('')
    }
  }

  const removeChapter = (index: number) => {
    setFormData(prev => ({
      ...prev,
      chapters: prev.chapters.filter((_, i) => i !== index)
    }))
  }

  const addTag = () => {
    if (newTag.trim() && !formData.tags.includes(newTag.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, newTag.trim()]
      }))
      setNewTag('')
    }
  }

  const removeTag = (index: number) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter((_, i) => i !== index)
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    setSuccess('')

    try {
      const response = await fetch(`/api/courses/${courseId}/books/${bookId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      if (response.ok) {
        setSuccess('Libro aggiornato con successo!')
        setTimeout(() => {
          router.push(`/courses/${courseId}/books/${bookId}`)
        }, 1500)
      } else {
        setError('Errore durante l\'aggiornamento del libro')
      }
    } catch (error) {
      setError('Errore durante l\'aggiornamento del libro')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600">Caricamento...</p>
        </div>
      </div>
    )
  }

  if (!book) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="text-center">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Libro non trovato</h3>
          <p className="text-gray-600 mb-4">Il libro richiesto non è disponibile</p>
          <Link
            href={`/courses/${courseId}/books`}
            className="text-blue-600 hover:text-blue-700"
          >
            ← Torna ai libri
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container-responsive py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-4 mb-4">
            <Link
              href={`/courses/${courseId}/books/${bookId}`}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="h-5 w-5 text-gray-600" />
            </Link>
            <div className="flex-1">
              <nav className="text-sm text-gray-500 mb-2">
                <Link href={`/courses/${courseId}`} className="hover:text-gray-700">
                  {courseName}
                </Link>
                <span className="mx-2">/</span>
                <Link href={`/courses/${courseId}/books`} className="hover:text-gray-700">
                  Libri
                </Link>
                <span className="mx-2">/</span>
                <Link href={`/courses/${courseId}/books/${bookId}`} className="hover:text-gray-700">
                  {book.title}
                </Link>
                <span className="mx-2">/</span>
                <span className="text-gray-900">Modifica</span>
              </nav>
              <h1 className="text-3xl font-bold text-gray-900">Modifica Libro</h1>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-6">
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Informazioni Generali */}
          <div className="bg-white p-6 rounded-xl shadow-sm border">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Informazioni Generali</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                  Titolo *
                </label>
                <input
                  type="text"
                  id="title"
                  name="title"
                  value={formData.title}
                  onChange={handleInputChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label htmlFor="author" className="block text-sm font-medium text-gray-700 mb-2">
                  Autore
                </label>
                <input
                  type="text"
                  id="author"
                  name="author"
                  value={formData.author}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label htmlFor="isbn" className="block text-sm font-medium text-gray-700 mb-2">
                  ISBN
                </label>
                <input
                  type="text"
                  id="isbn"
                  name="isbn"
                  value={formData.isbn}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label htmlFor="year" className="block text-sm font-medium text-gray-700 mb-2">
                  Anno
                </label>
                <input
                  type="text"
                  id="year"
                  name="year"
                  value={formData.year}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label htmlFor="publisher" className="block text-sm font-medium text-gray-700 mb-2">
                  Editore
                </label>
                <input
                  type="text"
                  id="publisher"
                  name="publisher"
                  value={formData.publisher}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            <div className="mt-6">
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                Descrizione
              </label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Capitoli */}
          <div className="bg-white p-6 rounded-xl shadow-sm border">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Capitoli</h2>

            <div className="space-y-3">
              {formData.chapters.map((chapter, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                    {index + 1}
                  </div>
                  <span className="flex-1 text-gray-700">{chapter}</span>
                  <button
                    type="button"
                    onClick={() => removeChapter(index)}
                    className="p-1 text-red-600 hover:bg-red-50 rounded"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>

            <div className="mt-4 flex items-center space-x-3">
              <input
                type="text"
                value={newChapter}
                onChange={(e) => setNewChapter(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addChapter())}
                placeholder="Aggiungi un nuovo capitolo"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <button
                type="button"
                onClick={addChapter}
                className="btn btn-secondary flex items-center space-x-2"
              >
                <Plus className="h-4 w-4" />
                <span>Aggiungi</span>
              </button>
            </div>
          </div>

          {/* Tag */}
          <div className="bg-white p-6 rounded-xl shadow-sm border">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Tag</h2>

            <div className="flex flex-wrap gap-2 mb-4">
              {formData.tags.map((tag, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-700 text-sm rounded-full"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => removeTag(index)}
                    className="ml-2 text-blue-600 hover:text-blue-800"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>

            <div className="flex items-center space-x-3">
              <input
                type="text"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                placeholder="Aggiungi un tag"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <button
                type="button"
                onClick={addTag}
                className="btn btn-secondary flex items-center space-x-2"
              >
                <Plus className="h-4 w-4" />
                <span>Aggiungi</span>
              </button>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-4">
            <Link
              href={`/courses/${courseId}/books/${bookId}`}
              className="btn btn-secondary"
            >
              Annulla
            </Link>
            <button
              type="submit"
              disabled={saving}
              className="btn btn-primary flex items-center space-x-2"
            >
              <Save className="h-4 w-4" />
              <span>{saving ? 'Salvataggio...' : 'Salva Modifiche'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}