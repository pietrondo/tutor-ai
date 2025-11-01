'use client'

import { useState, useEffect } from 'react'
import {
  Brain,
  FileQuestion,
  Target,
  Clock,
  CheckCircle,
  AlertCircle,
  Play,
  RefreshCw,
  BookOpen,
  TrendingUp,
  Zap
} from 'lucide-react'
import { useConceptKnowledge } from '@/hooks/useConceptKnowledge'
import { TestQuestion, Concept } from '@/types/indexing'

interface TestGenerationPanelProps {
  courseId: string
  onTestGenerated?: (questions: TestQuestion[]) => void
}

interface TestConfiguration {
  conceptIds: string[]
  count: number
  difficulty: number
  questionTypes: string[]
  timeLimit: number
  includeExplanations: boolean
  includeHints: boolean
}

export function TestGenerationPanel({ courseId, onTestGenerated }: TestGenerationPanelProps) {
  const {
    concepts,
    testQuestions,
    isLoading,
    error,
    fetchConcepts,
    generateTestQuestions,
    updateConceptMastery,
    getStudyRecommendations
  } = useConceptKnowledge()

  const [configuration, setConfiguration] = useState<TestConfiguration>({
    conceptIds: [],
    count: 10,
    difficulty: 3,
    questionTypes: ['multiple_choice', 'true_false', 'short_answer'],
    timeLimit: 600,
    includeExplanations: true,
    includeHints: false
  })

  const [selectedConcepts, setSelectedConcepts] = useState<string[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [testResults, setTestResults] = useState<any[]>([])
  const [showPreview, setShowPreview] = useState(false)

  useEffect(() => {
    if (courseId) {
      fetchConcepts(courseId)
    }
  }, [courseId, fetchConcepts])

  const handleGenerateTest = async () => {
    if (configuration.conceptIds.length === 0) {
      alert('Seleziona almeno un concetto per generare il test')
      return
    }

    try {
      setIsGenerating(true)
      await generateTestQuestions(configuration.conceptIds, configuration.count, configuration.difficulty)

      if (onTestGenerated) {
        onTestGenerated(testQuestions)
      }

      setShowPreview(true)
    } catch (err) {
      console.error('Error generating test:', err)
    } finally {
      setIsGenerating(false)
    }
  }

  const toggleConcept = (conceptId: string) => {
    const newConceptIds = configuration.conceptIds.includes(conceptId)
      ? configuration.conceptIds.filter(id => id !== conceptId)
      : [...configuration.conceptIds, conceptId]

    setConfiguration({
      ...configuration,
      conceptIds: newConceptIds
    })
  }

  const getDifficultyColor = (level: number) => {
    switch (level) {
      case 1: return 'bg-green-100 text-green-800'
      case 2: return 'bg-blue-100 text-blue-800'
      case 3: return 'bg-yellow-100 text-yellow-800'
      case 4: return 'bg-orange-100 text-orange-800'
      case 5: return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getDifficultyLabel = (level: number) => {
    switch (level) {
      case 1: return 'Molto Facile'
      case 2: return 'Facile'
      case 3: return 'Medio'
      case 4: return 'Difficile'
      case 5: return 'Molto Difficile'
      default: return 'Sconosciuto'
    }
  }

  const getQuestionTypeIcon = (type: string) => {
    switch (type) {
      case 'multiple_choice': return <Target className="h-4 w-4" />
      case 'true_false': return <CheckCircle className="h-4 w-4" />
      case 'short_answer': return <BookOpen className="h-4 w-4" />
      case 'essay': return <FileQuestion className="h-4 w-4" />
      default: return <Brain className="h-4 w-4" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-xl">
              <Brain className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-lg text-gray-900">
                Generatore di Test Automatici
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Crea test personalizzati basati sui concetti del corso
              </p>
            </div>
          </div>
          <button
            onClick={handleGenerateTest}
            disabled={isGenerating || configuration.conceptIds.length === 0}
            className="btn btn-primary"
          >
            {isGenerating ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Generazione in corso...
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Genera Test
              </>
            )}
          </button>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {concepts.length}
            </div>
            <p className="text-xs text-gray-500">Concetti disponibili</p>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {configuration.conceptIds.length}
            </div>
            <p className="text-xs text-gray-500">Concetti selezionati</p>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {configuration.count}
            </div>
            <p className="text-xs text-gray-500">Domande</p>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {Math.round(configuration.timeLimit / 60)}m
            </div>
            <p className="text-xs text-gray-500">Tempo limite</p>
          </div>
        </div>
      </div>

      {/* Configuration */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <h4 className="font-semibold text-gray-900 mb-4">Configurazione Test</h4>

        {/* Concept Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Seleziona Concetti
          </label>
          <div className="space-y-2 max-h-48 overflow-y-auto pr-2">
            {concepts.map((concept) => (
              <div
                key={concept.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                onClick={() => toggleConcept(concept.id)}
              >
                <div className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={configuration.conceptIds.includes(concept.id)}
                    onChange={() => {}}
                    className="form-checkbox"
                  />
                  <div>
                    <div className="font-medium text-gray-900">
                      {concept.name}
                    </div>
                    <div className="text-xs text-gray-500">
                      {concept.category} • {concept.prerequisites.length} prerequisiti
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`badge badge-secondary text-xs ${getDifficultyColor(concept.difficulty)}`}>
                    {getDifficultyLabel(concept.difficulty)}
                  </span>
                  {concept.mastery_level && (
                    <div className="flex items-center space-x-1">
                      <TrendingUp className="h-3 w-3 text-blue-500" />
                      <span className="text-xs text-gray-600">
                        {Math.round(concept.mastery_level * 100)}%
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Test Options */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Numero di Domande
            </label>
            <input
              type="number"
              min="1"
              max="50"
              value={configuration.count}
              onChange={(e) => setConfiguration({
                ...configuration,
                count: parseInt(e.target.value) || 10
              })}
              className="form-input"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Difficoltà
            </label>
            <select
              value={configuration.difficulty}
              onChange={(e) => setConfiguration({
                ...configuration,
                difficulty: parseInt(e.target.value)
              })}
              className="form-input"
            >
              <option value={1}>Molto Facile</option>
              <option value={2}>Facile</option>
              <option value={3}>Medio</option>
              <option value={4}>Difficile</option>
              <option value={5}>Molto Difficile</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tempo Limite (minuti)
            </label>
            <input
              type="number"
              min="5"
              max="180"
              value={Math.round(configuration.timeLimit / 60)}
              onChange={(e) => setConfiguration({
                ...configuration,
                timeLimit: parseInt(e.target.value) * 60
              })}
              className="form-input"
            />
          </div>
        </div>

        {/* Question Types */}
        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Tipi di Domande
          </label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {[
              { value: 'multiple_choice', label: 'Scelta Multipla' },
              { value: 'true_false', label: 'Vero/Falso' },
              { value: 'short_answer', label: 'Risposta Breve' },
              { value: 'essay', label: 'Saggio' },
              { value: 'fill_blank', label: 'Completa Spazio' },
              { value: 'matching', label: 'Abbinamento' }
            ].map((type) => (
              <label key={type.value} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={configuration.questionTypes.includes(type.value)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setConfiguration({
                        ...configuration,
                        questionTypes: [...configuration.questionTypes, type.value]
                      })
                    } else {
                      setConfiguration({
                        ...configuration,
                        questionTypes: configuration.questionTypes.filter(t => t !== type.value)
                      })
                    }
                  }}
                  className="form-checkbox"
                />
                <div className="flex items-center space-x-2">
                  {getQuestionTypeIcon(type.value)}
                  <span className="text-sm text-gray-700">{type.label}</span>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Additional Options */}
        <div className="mt-4 flex space-x-4">
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={configuration.includeExplanations}
              onChange={(e) => setConfiguration({
                ...configuration,
                includeExplanations: e.target.checked
              })}
              className="form-checkbox"
            />
            <span className="text-sm text-gray-700">Includi spiegazioni</span>
          </label>
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={configuration.includeHints}
              onChange={(e) => setConfiguration({
                ...configuration,
                includeHints: e.target.checked
              })}
              className="form-checkbox"
            />
            <span className="text-sm text-gray-700">Includi suggerimenti</span>
          </label>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="alert alert-danger">
          <AlertCircle className="h-4 w-4 mr-2" />
          Errore: {error}
        </div>
      )}

      {/* Generated Questions Preview */}
      {showPreview && testQuestions.length > 0 && (
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-semibold text-gray-900">
              Test Generato ({testQuestions.length} domande)
            </h4>
            <button
              onClick={() => setShowPreview(false)}
              className="btn btn-ghost btn-sm"
            >
              Chiudi
            </button>
          </div>

          <div className="space-y-4 max-h-96 overflow-y-auto">
            {testQuestions.map((question, index) => (
              <div
                key={question.id}
                className="p-4 bg-white rounded-xl border border-gray-200"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-gray-500">
                      #{index + 1}
                    </span>
                    {getQuestionTypeIcon(question.type)}
                    <span className={`badge badge-primary text-xs ${getDifficultyColor(question.difficulty)}`}>
                      {getDifficultyLabel(question.difficulty)}
                    </span>
                    <span className="text-xs text-gray-500">
                      {question.points} punti
                    </span>
                  </div>
                  {question.time_limit && (
                    <div className="flex items-center space-x-1 text-xs text-gray-500">
                      <Clock className="h-3 w-3" />
                      <span>{question.time_limit}s</span>
                    </div>
                  )}
                </div>

                <div className="text-gray-900 font-medium mb-3">
                  {question.question}
                </div>

                {question.options && (
                  <div className="space-y-2 mb-3">
                    {question.options.map((option, optIndex) => (
                      <div
                        key={optIndex}
                        className={`p-2 rounded-lg border ${
                          optIndex === 0 ? 'bg-green-50 border-green-200 text-green-800' : 'bg-gray-50 border-gray-200'
                        }`}
                      >
                        {option}
                      </div>
                    ))}
                  </div>
                )}

                {question.explanation && (
                  <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="flex items-center space-x-2 mb-1">
                      <Zap className="h-4 w-4 text-blue-600" />
                      <span className="text-sm font-medium text-blue-800">
                        Spiegazione
                      </span>
                    </div>
                    <p className="text-sm text-blue-700">
                      {question.explanation}
                    </p>
                  </div>
                )}

                {question.hints && question.hints.length > 0 && (
                  <div className="mt-3 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                    <div className="text-sm font-medium text-yellow-800 mb-1">
                      Suggerimenti:
                    </div>
                    <ul className="space-y-1">
                      {question.hints.map((hint, hintIndex) => (
                        <li key={hintIndex} className="text-sm text-yellow-700">
                          • {hint}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}