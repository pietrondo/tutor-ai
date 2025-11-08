'use client'

import { useState, useMemo } from 'react'
import {
  Brain,
  Target,
  CheckCircle2,
  Circle,
  Zap,
  Clock,
  TrendingUp,
  ChevronRight,
  ChevronDown,
  Book,
  Sparkles,
  Award,
  BarChart3
} from 'lucide-react'
import type { CourseConcept, CourseConceptMap, ConceptMetrics } from '@/types/concept'

interface ConceptVisualMapProps {
  conceptMap: CourseConceptMap | null
  conceptMetrics: ConceptMetrics
  conceptsLoading: boolean
  conceptsGenerating: boolean
  onConceptToggle: (conceptId: string) => void
  selectedConceptIds: string[]
  onConceptQuiz?: (concept: CourseConcept) => void
  expandedByDefault?: boolean
}

interface ConceptProgress {
  id: string
  name: string
  mastery: number
  attempts: number
  avgTime: number
  lastAttempt?: string
  trend: 'up' | 'down' | 'stable'
}

export function ConceptVisualMap({
  conceptMap,
  conceptMetrics,
  conceptsLoading,
  conceptsGenerating,
  onConceptToggle,
  selectedConceptIds,
  onConceptQuiz,
  expandedByDefault = true
}: ConceptVisualMapProps) {
  const [expanded, setExpanded] = useState(expandedByDefault)
  const [expandedChapters, setExpandedChapters] = useState<Set<string>>(new Set())

  const conceptsWithProgress = useMemo(() => {
    if (!conceptMap?.concepts) return []

    return conceptMap.concepts.map(concept => {
      const metrics = conceptMetrics[concept.id]
      const progress: ConceptProgress = {
        id: concept.id,
        name: concept.name,
        mastery: metrics ? metrics.stats.average_score * 100 : 0,
        attempts: metrics ? metrics.stats.attempts_count : 0,
        avgTime: metrics ? metrics.stats.average_time_seconds : 0,
        lastAttempt: metrics ? metrics.last_attempt : undefined,
        trend: metrics ? getTrendFromMetrics(metrics.stats) : 'stable'
      }
      return { concept, progress }
    })
  }, [conceptMap, conceptMetrics])

  const chaptersGrouped = useMemo(() => {
    const chapters = new Map<string, { title: string; index: number; concepts: Array<{ concept: CourseConcept; progress: ConceptProgress }> }>()

    conceptsWithProgress.forEach(({ concept, progress }) => {
      const chapterTitle = concept.chapter?.title || 'Generale'
      const chapterIndex = concept.chapter?.index || 999

      if (!chapters.has(chapterTitle)) {
        chapters.set(chapterTitle, {
          title: chapterTitle,
          index: chapterIndex,
          concepts: []
        })
      }

      chapters.get(chapterTitle)!.concepts.push({ concept, progress })
    })

    return Array.from(chapters.values()).sort((a, b) => a.index - b.index)
  }, [conceptsWithProgress])

  const toggleChapter = (chapterTitle: string) => {
    setExpandedChapters(prev => {
      const newSet = new Set(prev)
      if (newSet.has(chapterTitle)) {
        newSet.delete(chapterTitle)
      } else {
        newSet.add(chapterTitle)
      }
      return newSet
    })
  }

  const getMasteryColor = (mastery: number) => {
    if (mastery >= 80) return 'text-green-600 bg-green-50 border-green-200'
    if (mastery >= 60) return 'text-blue-600 bg-blue-50 border-blue-200'
    if (mastery >= 40) return 'text-yellow-600 bg-yellow-50 border-yellow-200'
    return 'text-red-600 bg-red-50 border-red-200'
  }

  const getMasteryIcon = (mastery: number, attempts: number) => {
    if (attempts === 0) return Circle
    if (mastery >= 80) return CheckCircle2
    if (mastery >= 60) return Target
    return Circle
  }

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up': return TrendingUp
      case 'down': return TrendingUp
      default: return Circle
    }
  }

  const getTrendColor = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up': return 'text-green-500'
      case 'down': return 'text-red-500'
      default: return 'text-gray-400'
    }
  }

  if (!expanded) {
    return (
      <div className="bg-white border rounded-xl shadow-sm p-4">
        <button
          onClick={() => setExpanded(true)}
          className="w-full flex items-center justify-between text-left hover:bg-gray-50 rounded-lg p-3 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <Brain className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Mappa Concettuale</h3>
              <p className="text-sm text-gray-500">
                {conceptsWithProgress.length} concetti • {conceptsWithProgress.filter(c => c.progress.attempts > 0).length} esplorati
              </p>
            </div>
          </div>
          <ChevronRight className="w-5 h-5 text-gray-400" />
        </button>
      </div>
    )
  }

  return (
    <div className="bg-white border rounded-xl shadow-sm">
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <Brain className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Mappa Concettuale</h3>
              <p className="text-sm text-gray-500">
                {conceptsLoading ? 'Caricamento...' : `${conceptsWithProgress.length} concetti`}
              </p>
            </div>
          </div>
          <button
            onClick={() => setExpanded(false)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ChevronDown className="w-4 h-4 text-gray-400" />
          </button>
        </div>

        {conceptsGenerating && (
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
            <div className="flex items-center gap-2 text-sm text-purple-700">
              <Sparkles className="w-4 h-4 animate-pulse" />
              <span>Generazione mappa in corso...</span>
            </div>
          </div>
        )}

        {conceptsWithProgress.length > 0 && (
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="bg-green-50 rounded-lg p-2">
              <div className="flex items-center justify-center gap-1 text-green-600">
                <CheckCircle2 className="w-3 h-3" />
                <span className="text-xs font-medium">
                  {conceptsWithProgress.filter(c => c.progress.mastery >= 80).length}
                </span>
              </div>
              <div className="text-xs text-green-700">Dominati</div>
            </div>
            <div className="bg-blue-50 rounded-lg p-2">
              <div className="flex items-center justify-center gap-1 text-blue-600">
                <Target className="w-3 h-3" />
                <span className="text-xs font-medium">
                  {conceptsWithProgress.filter(c => c.progress.mastery >= 40 && c.progress.mastery < 80).length}
                </span>
              </div>
              <div className="text-xs text-blue-700">In Progress</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-2">
              <div className="flex items-center justify-center gap-1 text-gray-600">
                <Circle className="w-3 h-3" />
                <span className="text-xs font-medium">
                  {conceptsWithProgress.filter(c => c.progress.attempts === 0).length}
                </span>
              </div>
              <div className="text-xs text-gray-700">Non Iniziati</div>
            </div>
          </div>
        )}
      </div>

      <div className="max-h-96 overflow-y-auto">
        {conceptsWithProgress.length === 0 && !conceptsLoading && !conceptsGenerating ? (
          <div className="p-8 text-center">
            <Brain className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 text-sm">Nessuna mappa concettuale disponibile</p>
            <p className="text-gray-400 text-xs mt-1">Genera una mappa per visualizzare i concetti chiave</p>
          </div>
        ) : (
          <div className="p-4 space-y-3">
            {chaptersGrouped.map((chapter) => (
              <div key={chapter.title} className="border border-gray-200 rounded-lg">
                <button
                  onClick={() => toggleChapter(chapter.title)}
                  className="w-full flex items-center justify-between p-3 hover:bg-gray-50 transition-colors rounded-t-lg"
                >
                  <div className="flex items-center gap-2">
                    <Book className="w-4 h-4 text-gray-500" />
                    <span className="font-medium text-sm text-gray-900">{chapter.title}</span>
                    <span className="text-xs text-gray-500">({chapter.concepts.length})</span>
                  </div>
                  {expandedChapters.has(chapter.title) ?
                    <ChevronDown className="w-4 h-4 text-gray-400" /> :
                    <ChevronRight className="w-4 h-4 text-gray-400" />
                  }
                </button>

                {expandedChapters.has(chapter.title) && (
                  <div className="border-t border-gray-200 p-3 space-y-2">
                    {chapter.concepts.map(({ concept, progress }) => {
                      const isSelected = selectedConceptIds.includes(concept.id)
                      const MasteryIcon = getMasteryIcon(progress.mastery, progress.attempts)
                      const TrendIcon = getTrendIcon(progress.trend)
                      const masteryColor = getMasteryColor(progress.mastery)

                      return (
                        <div
                          key={concept.id}
                          className={`border rounded-lg p-3 transition-all cursor-pointer hover:shadow-sm ${
                            isSelected
                              ? 'border-purple-300 bg-purple-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center gap-2 flex-1">
                              <button
                                onClick={() => onConceptToggle(concept.id)}
                                className={`p-1 rounded transition-colors ${
                                  isSelected
                                    ? 'bg-purple-200 text-purple-700'
                                    : 'hover:bg-gray-100'
                                }`}
                              >
                                <MasteryIcon className="w-4 h-4" />
                              </button>
                              <div className="flex-1">
                                <p className={`text-sm font-medium ${isSelected ? 'text-purple-900' : 'text-gray-900'}`}>
                                  {concept.name}
                                </p>
                                <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                                  {concept.summary}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              {progress.attempts > 0 && (
                                <div className={`px-2 py-1 rounded-full text-xs font-medium border ${masteryColor}`}>
                                  {progress.mastery.toFixed(0)}%
                                </div>
                              )}
                              {onConceptQuiz && (
                                <button
                                  onClick={() => onConceptQuiz(concept)}
                                  className="p-1 hover:bg-gray-100 rounded transition-colors"
                                  title="Genera quiz"
                                >
                                  <Zap className="w-4 h-4 text-blue-500" />
                                </button>
                              )}
                            </div>
                          </div>

                          {progress.attempts > 0 && (
                            <div className="flex items-center justify-between text-xs text-gray-500">
                              <div className="flex items-center gap-3">
                                <span className="flex items-center gap-1">
                                  <BarChart3 className="w-3 h-3" />
                                  {progress.attempts} tentativi
                                </span>
                                <span className="flex items-center gap-1">
                                  <Clock className="w-3 h-3" />
                                  {progress.avgTime.toFixed(0)}s media
                                </span>
                              </div>
                              <div className={`flex items-center gap-1 ${getTrendColor(progress.trend)}`}>
                                <TrendIcon className="w-3 h-3" />
                              </div>
                            </div>
                          )}

                          {progress.attempts > 0 && (
                            <div className="mt-2">
                              <div className="w-full bg-gray-200 rounded-full h-1.5">
                                <div
                                  className={`h-1.5 rounded-full transition-all duration-300 ${
                                    progress.mastery >= 80 ? 'bg-green-500' :
                                    progress.mastery >= 60 ? 'bg-blue-500' :
                                    progress.mastery >= 40 ? 'bg-yellow-500' : 'bg-red-500'
                                  }`}
                                  style={{ width: `${Math.min(progress.mastery, 100)}%` }}
                                />
                              </div>
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function getTrendFromMetrics(stats: any): 'up' | 'down' | 'stable' {
  // Questo è un placeholder - nell'implementazione reale dovremmo calcolare il trend
  // basandosi sulle performance recenti rispetto a quelle passate
  if (stats.average_score >= 0.8) return 'up'
  if (stats.average_score >= 0.6) return 'stable'
  return 'down'
}