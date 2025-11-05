'use client'

import { BookOpen, ChevronDown } from 'lucide-react'

interface Book {
  id: string
  title: string
  author?: string
  materials_count: number
}

interface BookSelectorProps {
  books: Book[]
  selectedBook: string
  onBookChange: (bookId: string) => void
}

export default function BookSelector({ books, selectedBook, onBookChange }: BookSelectorProps) {
  if (books.length === 0) {
    return null
  }

  return (
    <div className="mt-4">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        <BookOpen className="inline h-4 w-4 mr-1" />
        Seleziona Libro
      </label>
      <div className="relative">
        <select
          value={selectedBook}
          onChange={(e) => onBookChange(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none bg-white cursor-pointer"
        >
          <option value="">Nessun libro selezionato</option>
          {books.map((book) => (
            <option key={book.id} value={book.id}>
              {book.title}
              {book.author && ` - ${book.author}`}
              {book.materials_count > 0 && ` (${book.materials_count} materiali)`}
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
      </div>
    </div>
  )
}