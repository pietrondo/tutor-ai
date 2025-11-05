import React, { useState } from 'react'
import { Brain } from 'lucide-react'

interface SlideGeneratorProps {
  onGenerate?: (slides: unknown[]) => void
  bookId?: string
  courseId?: string
  bookTitle?: string
  bookAuthor?: string
}

const SlideGenerator: React.FC<SlideGeneratorProps> = ({ onGenerate }) => {
  const [generating, setGenerating] = useState(false)

  const handleGenerate = async () => {
    setGenerating(true)
    // Placeholder for slide generation
    setTimeout(() => {
      setGenerating(false)
      if (onGenerate) {
        onGenerate([])
      }
    }, 2000)
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Generatore Slide</h2>
        <Brain className="h-5 w-5 text-blue-600" />
      </div>

      <button
        onClick={handleGenerate}
        disabled={generating}
        className="w-full bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
      >
        {generating ? 'Generazione in corso...' : 'Genera Slide'}
      </button>
    </div>
  )
}

export default SlideGenerator
