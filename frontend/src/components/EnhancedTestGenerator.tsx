'use client'

import { useState, useEffect } from 'react'
import {
  Brain,
  Target,
  Zap,
  BookOpen,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Clock,
  Award,
  BarChart3,
  Cpu,
  FileText,
  RefreshCw,
  Settings,
  Play,
  Code,
  Lightbulb
} from 'lucide-react'
import { useConceptKnowledge } from '@/hooks/useContentIndexing'
import { TestQuestion, Concept } from '@/types/indexing'

interface EnhancedTestGeneratorProps {
  courseId: string
  concepts: Concept[]
  onTestGenerated?: (questions: EnhancedTestQuestion[]) => void
}

interface EnhancedTestQuestion extends TestQuestion {
  context7Enhancements: {
    latestPatterns: string[]
    codeExamples: CodeExample[]
    bestPractices: string[]
    industryRelevance: number
    realWorldApplications: string[]
  }
  adaptiveFeatures: {
    dynamicDifficulty: boolean
    personalizedHints: string[]
    alternativeExplanations: string[]
    prerequisiteCheck: boolean
  }
  analytics: {
    estimatedTime: number
    cognitiveLoad: number
    engagementScore: number
    learningObjective: string
  }
}

interface CodeExample {
  framework: string
  language: string
  snippet: string
  explanation: string
  difficulty: number
  concepts: string[]
}

interface TestPattern {
  name: string
  description: string
  difficulty: number
  frameworks: string[]
  useCases: string[]
  frequency: 'high' | 'medium' | 'low'
}

interface Context7TestConfig {
  includeCodeExamples: boolean
  adaptiveDifficulty: boolean
  personalizedHints: boolean
  industryRelevance: boolean
  realWorldApplications: boolean
  cognitiveLoadAnalysis: boolean
}

export function EnhancedTestGenerator({
  courseId,
  concepts,
  onTestGenerated
}: EnhancedTestGeneratorProps) {
  const {
    generateTestQuestions,
    testQuestions,
    isLoading,
    error
  } = useConceptKnowledge()

  const [enhancedQuestions, setEnhancedQuestions] = useState<EnhancedTestQuestion[]>([])
  const [selectedConcepts, setSelectedConcepts] = useState<string[]>([])
  const [testConfiguration, setTestConfiguration] = useState({
    count: 10,
    difficulty: 3,
    questionTypes: ['multiple_choice', 'short_answer', 'coding_challenge'],
    includeContext7: true,
    adaptiveMode: true
  })
  const [context7Config, setContext7Config] = useState<Context7TestConfig>({
    includeCodeExamples: true,
    adaptiveDifficulty: true,
    personalizedHints: true,
    industryRelevance: true,
    realWorldApplications: true,
    cognitiveLoadAnalysis: true
  })
  const [isGenerating, setIsGenerating] = useState(false)
  const [context7Progress, setContext7Progress] = useState(0)
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false)

  const generateEnhancedTest = async () => {
    if (selectedConcepts.length === 0) {
      alert('Seleziona almeno un concetto per generare il test')
      return
    }

    setIsGenerating(true)
    setContext7Progress(0)

    try {
      // Generate base questions
      await generateTestQuestions(selectedConcepts, testConfiguration.count, testConfiguration.difficulty)

      // Enhance with Context7
      if (testConfiguration.includeContext7) {
        const enhanced = await enhanceQuestionsWithContext7(testQuestions)
        setEnhancedQuestions(enhanced)

        if (onTestGenerated) {
          onTestGenerated(enhanced)
        }
      } else {
        // Convert basic questions to enhanced format without Context7
        const basicEnhanced = testQuestions.map(q => convertToEnhanced(q))
        setEnhancedQuestions(basicEnhanced)

        if (onTestGenerated) {
          onTestGenerated(basicEnhanced)
        }
      }

    } catch (err) {
      console.error('Error generating enhanced test:', err)
    } finally {
      setIsGenerating(false)
      setContext7Progress(0)
    }
  }

  const enhanceQuestionsWithContext7 = async (questions: TestQuestion[]): Promise<EnhancedTestQuestion[]> => {
    setContext7Progress(20)

    // Fetch latest test patterns and best practices
    const latestPatterns = await fetchLatestTestPatterns()
    setContext7Progress(40)

    // Get code examples for each question
    const enhancedQuestions = await Promise.all(
      questions.map(async (question, index) => {
        setContext7Progress(40 + (index * 40 / questions.length))

        const codeExamples = await fetchRelevantCodeExamples(question)
        const bestPractices = await fetchBestPracticesForConcept(question.concept_id)
        const realWorldApps = await fetchRealWorldApplications(question.concept_id)
        const analytics = await performAnalyticsAnalysis(question)

        return {
          ...question,
          context7Enhancements: {
            latestPatterns: latestPatterns.map(p => p.name),
            codeExamples,
            bestPractices,
            industryRelevance: calculateIndustryRelevance(question),
            realWorldApplications: realWorldApps
          },
          adaptiveFeatures: {
            dynamicDifficulty: context7Config.adaptiveDifficulty,
            personalizedHints: generatePersonalizedHints(question),
            alternativeExplanations: generateAlternativeExplanations(question),
            prerequisiteCheck: true
          },
          analytics
        }
      })
    )

    setContext7Progress(100)
    return enhancedQuestions
  }

  const convertToEnhanced = (question: TestQuestion): EnhancedTestQuestion => ({
    ...question,
    context7Enhancements: {
      latestPatterns: [],
      codeExamples: [],
      bestPractices: [],
      industryRelevance: 0.5,
      realWorldApplications: []
    },
    adaptiveFeatures: {
      dynamicDifficulty: false,
      personalizedHints: [],
      alternativeExplanations: [],
      prerequisiteCheck: false
    },
    analytics: {
      estimatedTime: question.time_limit || 60,
      cognitiveLoad: 0.5,
      engagementScore: 0.5,
      learningObjective: 'Test basic understanding'
    }
  })

  const fetchLatestTestPatterns = async (): Promise<TestPattern[]> => {
    // Simulate Context7 API call for latest test patterns
    await new Promise(resolve => setTimeout(resolve, 800))
    return [
      {
        name: 'Problem-Based Learning Assessment',
        description: 'Real-world problem scenarios with multiple solution paths',
        difficulty: 4,
        frameworks: ['React', 'Node.js'],
        useCases: ['Code review', 'System design', 'Debugging'],
        frequency: 'high'
      },
      {
        name: 'Interactive Code Challenges',
        description: 'Hands-on coding with immediate feedback',
        difficulty: 3,
        frameworks: ['JavaScript', 'TypeScript'],
        useCases: ['Algorithm implementation', 'API development'],
        frequency: 'high'
      },
      {
        name: 'Scenario-Based Testing',
        description: 'Contextual questions based on real development scenarios',
        difficulty: 3,
        frameworks: ['Next.js', 'Express'],
        useCases: ['Project architecture', 'Performance optimization'],
        frequency: 'medium'
      }
    ]
  }

  const fetchRelevantCodeExamples = async (question: TestQuestion): Promise<CodeExample[]> => {
    // Simulate Context7 API call for relevant code examples
    await new Promise(resolve => setTimeout(resolve, 300))
    return [
      {
        framework: 'React',
        language: 'TypeScript',
        snippet: 'const useEnhancedHook = <T>(initial: T) => {\n  const [state, setState] = useState(initial)\n  const enhanced = useMemo(() => enhance(state), [state])\n  return { state, setState, enhanced }\n}',
        explanation: 'Custom hook with TypeScript and memoization for performance',
        difficulty: 3,
        concepts: ['React Hooks', 'TypeScript', 'Performance']
      },
      {
        framework: 'Next.js',
        language: 'JavaScript',
        snippet: 'export default function EnhancedPage({ data }) {\n  return (\n    <Layout>\n      <EnhancedComponent data={data} />\n      <InteractiveTestSection />\n    </Layout>\n  )\n}',
        explanation: 'Server-side rendered page with enhanced components',
        difficulty: 2,
        concepts: ['SSR', 'Components', 'Data Fetching']
      }
    ]
  }

  const fetchBestPracticesForConcept = async (conceptId: string): Promise<string[]> => {
    await new Promise(resolve => setTimeout(resolve, 200))
    return [
      'Always validate inputs and handle edge cases',
      'Use meaningful variable and function names',
      'Follow SOLID principles for maintainable code',
      'Implement proper error handling and logging',
      'Write tests before implementing features (TDD)'
    ]
  }

  const fetchRealWorldApplications = async (conceptId: string): Promise<string[]> => {
    await new Promise(resolve => setTimeout(resolve, 150))
    return [
      'E-commerce platform development',
      'Real-time data visualization dashboards',
      'Content management systems',
      'API development and integration',
      'Mobile-responsive web applications'
    ]
  }

  const performAnalyticsAnalysis = async (question: TestQuestion): Promise<EnhancedTestQuestion['analytics']> => {
    await new Promise(resolve => setTimeout(resolve, 100))
    return {
      estimatedTime: question.time_limit || 60,
      cognitiveLoad: question.difficulty * 0.2,
      engagementScore: Math.random() * 0.5 + 0.5,
      learningObjective: `Master ${question.concept_id} concepts through practical application`
    }
  }

  const calculateIndustryRelevance = (question: TestQuestion): number => {
    // Simulate industry relevance calculation
    const baseRelevance = question.difficulty * 0.15
    const typeBonus = question.type === 'essay' ? 0.3 : 0.1
    return Math.min(1, baseRelevance + typeBonus + Math.random() * 0.2)
  }

  const generatePersonalizedHints = (question: TestQuestion): string[] => {
    return [
      'Think about the real-world applications of this concept',
      'Consider edge cases and error scenarios',
      'Break down the problem into smaller components',
      'Review the prerequisites before attempting the solution'
    ]
  }

  const generateAlternativeExplanations = (question: TestQuestion): string[] => {
    return [
      'Alternative approach: Consider this from a different perspective',
      'Simplified explanation: Think of this as a practical application',
      'Advanced concept: This relates to broader architectural patterns'
    ]
  }

  const toggleConcept = (conceptId: string) => {
    setSelectedConcepts(prev =>
      prev.includes(conceptId)
        ? prev.filter(id => id !== conceptId)
        : [...prev, conceptId]
    )
  }

  const renderEnhancedQuestion = (question: EnhancedTestQuestion, index: number) => (
    <div key={question.id} className="p-6 bg-white rounded-xl border border-gray-200 shadow-sm">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <span className="text-sm font-medium text-gray-500">#{index + 1}</span>
          <div className="flex items-center space-x-2">
            {context7Config.includeCodeExamples && question.context7Enhancements.codeExamples.length > 0 && (
              <div className="flex items-center space-x-1 text-blue-600">
                <Code className="h-4 w-4" />
                <span className="text-xs">Code</span>
              </div>
            )}
            {context7Config.industryRelevance && (
              <div className="flex items-center space-x-1 text-purple-600">
                <TrendingUp className="h-4 w-4" />
                <span className="text-xs">{Math.round(question.context7Enhancements.industryRelevance * 100)}%</span>
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`badge badge-primary text-xs ${
            question.difficulty <= 2 ? 'bg-green-100 text-green-800' :
            question.difficulty <= 3 ? 'bg-yellow-100 text-yellow-800' :
            'bg-red-100 text-red-800'
          }`}>
            Difficulty {question.difficulty}
          </span>
          <span className="text-xs text-gray-500">
            {question.analytics.estimatedTime}s
          </span>
        </div>
      </div>

      <div className="text-gray-900 font-medium mb-4">
        {question.question}
      </div>

      {/* Context7 Enhancements */}
      {question.context7Enhancements.codeExamples.length > 0 && (
        <div className="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center space-x-2 mb-3">
            <Code className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-medium text-blue-800">Code Example</span>
          </div>
          {question.context7Enhancements.codeExamples[0] && (
            <div className="mb-3">
              <div className="text-xs text-blue-700 mb-1">{question.context7Enhancements.codeExamples[0].framework}</div>
              <div className="bg-gray-900 text-gray-100 p-3 rounded-lg font-mono text-sm overflow-x-auto">
                <pre>{question.context7Enhancements.codeExamples[0].snippet}</pre>
              </div>
              <p className="text-xs text-blue-700 mt-2">{question.context7Enhancements.codeExamples[0].explanation}</p>
            </div>
          )}
        </div>
      )}

      {/* Real World Applications */}
      {question.context7Enhancements.realWorldApplications.length > 0 && (
        <div className="mb-4 p-4 bg-green-50 rounded-lg border border-green-200">
          <div className="flex items-center space-x-2 mb-2">
            <Lightbulb className="h-4 w-4 text-green-600" />
            <span className="text-sm font-medium text-green-800">Real World Applications</span>
          </div>
          <ul className="space-y-1">
            {question.context7Enhancements.realWorldApplications.slice(0, 3).map((app, idx) => (
              <li key={idx} className="text-sm text-green-700 flex items-start">
                <span className="text-green-500 mr-2">•</span>
                {app}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Best Practices */}
      {question.context7Enhancements.bestPractices.length > 0 && (
        <div className="mb-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
          <div className="flex items-center space-x-2 mb-2">
            <Award className="h-4 w-4 text-purple-600" />
            <span className="text-sm font-medium text-purple-800">Best Practices</span>
          </div>
          <ul className="space-y-1">
            {question.context7Enhancements.bestPractices.slice(0, 2).map((practice, idx) => (
              <li key={idx} className="text-sm text-purple-700 flex items-start">
                <CheckCircle className="h-3 w-3 text-purple-500 mr-2 mt-0.5 flex-shrink-0" />
                {practice}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Options or Input Area */}
      {question.options && (
        <div className="space-y-2 mb-4">
          {question.options.map((option, optIndex) => (
            <div
              key={optIndex}
              className={`p-3 rounded-lg border cursor-pointer transition-all duration-200 hover:border-blue-300 hover:bg-blue-50 ${
                optIndex === 0 ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'
              }`}
            >
              {option}
            </div>
          ))}
        </div>
      )}

      {/* Analytics Footer */}
      {context7Config.cognitiveLoadAnalysis && (
        <div className="flex items-center justify-between text-xs text-gray-500 border-t pt-3">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1">
              <Clock className="h-3 w-3" />
              <span>{question.analytics.estimatedTime}s</span>
            </div>
            <div className="flex items-center space-x-1">
              <Brain className="h-3 w-3" />
              <span>Cognitive Load: {Math.round(question.analytics.cognitiveLoad * 100)}%</span>
            </div>
            <div className="flex items-center space-x-1">
              <BarChart3 className="h-3 w-3" />
              <span>Engagement: {Math.round(question.analytics.engagementScore * 100)}%</span>
            </div>
          </div>
          <div className="text-gray-600">
            {question.analytics.learningObjective}
          </div>
        </div>
      )}
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl">
              <Cpu className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-lg text-gray-900">
                Enhanced Test Generator
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Generazione test potenziata con Context7 MCP e pattern attuali
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
              className="btn btn-secondary btn-sm"
            >
              <Settings className="h-4 w-4 mr-2" />
              Opzioni Avanzate
            </button>
          </div>
        </div>

        {/* Progress Bar */}
        {isGenerating && (
          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">Generazione Enhanced Test</span>
              <span className="text-sm text-purple-600">{context7Progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-purple-500 to-pink-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${context7Progress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Configuration */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <h4 className="font-semibold text-gray-900 mb-4">Configurazione Test</h4>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Numero di Domande
            </label>
            <input
              type="number"
              min="1"
              max="20"
              value={testConfiguration.count}
              onChange={(e) => setTestConfiguration(prev => ({
                ...prev,
                count: parseInt(e.target.value) || 10
              }))}
              className="form-input"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Difficoltà Base
            </label>
            <select
              value={testConfiguration.difficulty}
              onChange={(e) => setTestConfiguration(prev => ({
                ...prev,
                difficulty: parseInt(e.target.value)
              }))}
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
              Tipi di Domande
            </label>
            <select
              multiple
              value={testConfiguration.questionTypes}
              onChange={(e) => {
                const values = Array.from(e.target.selectedOptions, option => option.value)
                setTestConfiguration(prev => ({ ...prev, questionTypes: values }))
              }}
              className="form-input"
              size={3}
            >
              <option value="multiple_choice">Scelta Multipla</option>
              <option value="short_answer">Risposta Breve</option>
              <option value="coding_challenge">Coding Challenge</option>
              <option value="scenario_based">Scenario Based</option>
            </select>
          </div>
        </div>

        <div className="flex items-center space-x-4 mb-6">
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={testConfiguration.includeContext7}
              onChange={(e) => setTestConfiguration(prev => ({
                ...prev,
                includeContext7: e.target.checked
              }))}
              className="form-checkbox"
            />
            <span className="text-sm text-gray-700">Includi Context7 Enhancements</span>
          </label>
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={testConfiguration.adaptiveMode}
              onChange={(e) => setTestConfiguration(prev => ({
                ...prev,
                adaptiveMode: e.target.checked
              }))}
              className="form-checkbox"
            />
            <span className="text-sm text-gray-700">Modalità Adaptiva</span>
          </label>
        </div>

        {/* Concept Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Seleziona Concetti ({selectedConcepts.length})
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-64 overflow-y-auto">
            {concepts.map((concept) => (
              <div
                key={concept.id}
                className={`p-3 rounded-lg border cursor-pointer transition-all duration-200 ${
                  selectedConcepts.includes(concept.id)
                    ? 'border-purple-300 bg-purple-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => toggleConcept(concept.id)}
              >
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={selectedConcepts.includes(concept.id)}
                    onChange={() => {}}
                    className="form-checkbox"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{concept.name}</div>
                    <div className="text-xs text-gray-500">
                      {concept.category} • Difficulty: {concept.difficulty}/5
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-6 flex justify-center">
          <button
            onClick={generateEnhancedTest}
            disabled={isGenerating || selectedConcepts.length === 0}
            className="btn btn-primary"
          >
            {isGenerating ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Generazione Enhanced Test...
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Genera Test Enhanced ({testConfiguration.count} domande)
              </>
            )}
          </button>
        </div>
      </div>

      {/* Advanced Options */}
      {showAdvancedOptions && (
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <h4 className="font-semibold text-gray-900 mb-4">Opzioni Context7 Avanzate</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(context7Config).map(([key, value]) => (
              <label key={key} className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={value}
                  onChange={(e) => setContext7Config(prev => ({ ...prev, [key]: e.target.checked }))}
                  className="form-checkbox"
                />
                <span className="text-sm text-gray-700">
                  {key === 'includeCodeExamples' ? 'Includi Esempi di Codice' :
                   key === 'adaptiveDifficulty' ? 'Difficoltà Adaptiva' :
                   key === 'personalizedHints' ? 'Suggerimenti Personalizzati' :
                   key === 'industryRelevance' ? 'Rilevanza Industriale' :
                   key === 'realWorldApplications' ? 'Applicazioni Real-World' :
                   'Analisi Cognitive Load'}
                </span>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Generated Questions */}
      {enhancedQuestions.length > 0 && (
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-semibold text-gray-900">
              Test Enhanced Generato ({enhancedQuestions.length} domande)
            </h4>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Cpu className="h-4 w-4" />
              <span>Context7 Enhanced</span>
            </div>
          </div>

          <div className="space-y-6 max-h-96 overflow-y-auto">
            {enhancedQuestions.map((question, index) => renderEnhancedQuestion(question, index))}
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="alert alert-danger">
          <AlertCircle className="h-4 w-4 mr-2" />
          Errore: {error}
        </div>
      )}
    </div>
  )
}