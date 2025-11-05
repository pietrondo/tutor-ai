'use client'

import { useState } from 'react'
import { Loader2 } from 'lucide-react'

interface ZAISlideGeneratorProps {
  courseId: string
  bookId?: string
  onSlidesGenerated?: (slides: unknown[]) => void
}

const ZAISlideGenerator = ({ courseId, bookId, onSlidesGenerated }: ZAISlideGeneratorProps) => {
  const [isGenerating, setIsGenerating] = useState(false)

  const handleGenerate = async () => {
    if (!courseId) {
      return
    }

    setIsGenerating(true)

    try {
      // Placeholder: in a full implementation this would call the backend
      await new Promise((resolve) => setTimeout(resolve, 1500))
      onSlidesGenerated?.([])
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="space-y-4">
      <button
        onClick={handleGenerate}
        disabled={isGenerating || !courseId}
        className="w-full rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-purple-700 disabled:opacity-60"
      >
        {isGenerating ? (
          <span className="flex items-center justify-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            Generazione in corso…
          </span>
        ) : (
          'Genera slide con l\'AI'
        )}
      </button>

      {bookId ? (
        <p className="text-xs text-gray-500">
          Le slide verranno basate sui materiali associati al libro selezionato.
        </p>
      ) : (
        <p className="text-xs text-gray-500">
          Seleziona un libro per generare slide specifiche, oppure genera un riassunto del corso.
        </p>
      )}
    </div>
  )
}

export default ZAISlideGenerator
