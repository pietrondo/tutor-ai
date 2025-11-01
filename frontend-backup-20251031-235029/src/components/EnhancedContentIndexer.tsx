'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  Brain,
  Zap,
  BookOpen,
  Target,
  TrendingUp,
  Database,
  Cloud,
  Cpu,
  FileText,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  BarChart3,
  Settings,
  Play,
  ArrowSync
} from 'lucide-react'
import { useContentIndexing } from '@/hooks/useContentIndexing'
import { MaterialIndexingStatus, ContentAnalysisResult, Concept } from '@/types/indexing'

interface EnhancedContentIndexerProps {
  courseId: string
  materials: Array<{
    id: string
    name: string
    type: string
    size: number
    lastModified: string
    indexingStatus?: MaterialIndexingStatus
  }>
  onIndexingComplete?: (materialId: string, enhancedAnalysis: EnhancedAnalysisResult) => void
}

interface EnhancedAnalysisResult extends ContentAnalysisResult {
  context7Insights: {
    latestBestPractices: string[]
    relatedFrameworks: string[]
    codeExamples: CodeExample[]
    currentTrends: string[]
  }
  aiRecommendations: {
    studyPath: string[]
    difficultyAdjustments: Record<string, number>
    relatedTopics: string[]
  }
  semanticAnalysis: {
    keyPhrases: string[]
    entities: Entity[]
    sentiment: 'positive' | 'neutral' | 'negative'
    complexity: number
  }
}

interface CodeExample {
  framework: string
  language: string
  snippet: string
  description: string
  difficulty: number
  concepts: string[]
}

interface Entity {
  name: string
  type: 'person' | 'organization' | 'location' | 'concept' | 'technology'
  confidence: number
}

interface Context7Request {
  materialContent: string
  concepts: string[]
  frameworks: string[]
  difficulty: number
}

export function EnhancedContentIndexer({
  courseId,
  materials,
  onIndexingComplete
}: EnhancedContentIndexerProps) {
  const {
    startIndexing,
    checkIndexingStatus,
    indexingStatus,
    isIndexing
  } = useContentIndexing()

  const [enhancedAnalysis, setEnhancedAnalysis] = useState<EnhancedAnalysisResult | null>(null)
  const [isContext7Active, setIsContext7Active] = useState(false)
  const [context7Progress, setContext7Progress] = useState(0)
  const [selectedMaterial, setSelectedMaterial] = useState<string | null>(null)
  const [context7Config, setContext7Config] = useState({
    includeCodeExamples: true,
    fetchLatestTrends: true,
    analyzeComplexity: true,
    generateRecommendations: true,
    semanticAnalysis: true
  })

  const enhanceWithContext7 = async (materialId: string, baseAnalysis: ContentAnalysisResult) => {
    setIsContext7Active(true)
    setContext7Progress(0)

    try {
      const material = materials.find(m => m.id === materialId)
      if (!material) throw new Error('Material not found')

      // Simulate Context7 API calls for enhanced analysis
      const context7Request: Context7Request = {
        materialContent: baseAnalysis.summary,
        concepts: baseAnalysis.key_concepts,
        frameworks: extractFrameworks(baseAnalysis),
        difficulty: getAverageDifficulty(baseAnalysis)
      }

      setContext7Progress(20)

      // Fetch latest best practices using Context7
      const latestBestPractices = await fetchLatestBestPractices(context7Request)
      setContext7Progress(40)

      // Get code examples and related frameworks
      const codeExamples = await fetchCodeExamples(context7Request)
      const relatedFrameworks = await fetchRelatedFrameworks(context7Request)
      setContext7Progress(60)

      // Analyze current trends
      const currentTrends = await fetchCurrentTrends(context7Request)
      setContext7Progress(80)

      // Generate AI recommendations
      const aiRecommendations = await generateAIRecommendations(baseAnalysis, latestBestPractices)
      setContext7Progress(90)

      // Perform semantic analysis
      const semanticAnalysis = await performSemanticAnalysis(baseAnalysis)
      setContext7Progress(100)

      const enhanced: EnhancedAnalysisResult = {
        ...baseAnalysis,
        context7Insights: {
          latestBestPractices,
          relatedFrameworks,
          codeExamples,
          currentTrends
        },
        aiRecommendations,
        semanticAnalysis
      }

      setEnhancedAnalysis(enhanced)
      return enhanced

    } catch (error) {
      console.error('Error in Context7 enhancement:', error)
      throw error
    } finally {
      setIsContext7Active(false)
      setContext7Progress(0)
    }
  }

  const fetchLatestBestPractices = async (request: Context7Request): Promise<string[]> => {
    // Simulate Context7 API call for best practices
    await new Promise(resolve => setTimeout(resolve, 1000))
    return [
      'Use modern ES6+ features for better code readability',
      'Implement proper error handling with try-catch blocks',
      'Follow responsive design principles for cross-device compatibility',
      'Optimize performance with lazy loading and code splitting',
      'Implement proper security measures and validation'
    ]
  }

  const fetchCodeExamples = async (request: Context7Request): Promise<CodeExample[]> => {
    // Simulate Context7 API call for code examples
    await new Promise(resolve => setTimeout(resolve, 800))
    return [
      {
        framework: 'React',
        language: 'TypeScript',
        snippet: 'const Component: React.FC<Props> = ({ data }) => {\n  return <div>{data.map(item => <Item key={item.id} {...item} />)}</div>\n}',
        description: 'Functional component with TypeScript and proper key handling',
        difficulty: 2,
        concepts: ['React Components', 'TypeScript', 'Props']
      },
      {
        framework: 'Next.js',
        language: 'JavaScript',
        snippet: 'export async function getServerSideProps() {\n  const data = await fetchData()\n  return { props: { data } }\n}',
        description: 'Server-side rendering with data fetching',
        difficulty: 3,
        concepts: ['SSR', 'Data Fetching', 'Next.js']
      }
    ]
  }

  const fetchRelatedFrameworks = async (request: Context7Request): Promise<string[]> => {
    // Simulate Context7 API call for related frameworks
    await new Promise(resolve => setTimeout(resolve, 600))
    return ['React', 'Next.js', 'TypeScript', 'Tailwind CSS', 'Node.js', 'Express']
  }

  const fetchCurrentTrends = async (request: Context7Request): Promise<string[]> => {
    // Simulate Context7 API call for current trends
    await new Promise(resolve => setTimeout(resolve, 700))
    return [
      'AI-powered development tools integration',
      'Serverless architecture adoption',
      'Progressive Web Apps (PWA) dominance',
      'Microservices and container orchestration',
      'Low-code/no-code platforms evolution'
    ]
  }

  const generateAIRecommendations = async (
    baseAnalysis: ContentAnalysisResult,
    bestPractices: string[]
  ): Promise<EnhancedAnalysisResult['aiRecommendations']> => {
    await new Promise(resolve => setTimeout(resolve, 500))
    return {
      studyPath: baseAnalysis.learning_objectives.slice(0, 3),
      difficultyAdjustments: Object.fromEntries(
        Object.entries(baseAnalysis.difficulty_distribution).map(([level, count]) => [
          level,
          count > 5 ? 0.8 : 1.2
        ])
      ),
      relatedTopics: ['Web Performance', 'Security Best Practices', 'Testing Strategies']
    }
  }

  const performSemanticAnalysis = async (baseAnalysis: ContentAnalysisResult): Promise<EnhancedAnalysisResult['semanticAnalysis']> => {
    await new Promise(resolve => setTimeout(resolve, 400))
    return {
      keyPhrases: baseAnalysis.key_concepts.slice(0, 10),
      entities: baseAnalysis.key_concepts.map(concept => ({
        name: concept,
        type: 'concept' as const,
        confidence: Math.random() * 0.5 + 0.5
      })),
      sentiment: 'positive',
      complexity: baseAnalysis.estimated_study_time / 60 // hours as complexity indicator
    }
  }

  const extractFrameworks = (analysis: ContentAnalysisResult): string[] => {
    // Extract frameworks based on content analysis
    const frameworks: string[] = []
    const content = analysis.summary.toLowerCase()

    if (content.includes('react') || content.includes('component')) frameworks.push('React')
    if (content.includes('next') || content.includes('ssr')) frameworks.push('Next.js')
    if (content.includes('typescript') || content.includes('type')) frameworks.push('TypeScript')
    if (content.includes('tailwind') || content.includes('css')) frameworks.push('Tailwind CSS')

    return frameworks
  }

  const getAverageDifficulty = (analysis: ContentAnalysisResult): number => {
    const totalItems = Object.values(analysis.difficulty_distribution).reduce((sum, count) => sum + count, 0)
    const weightedSum = Object.entries(analysis.difficulty_distribution).reduce(
      (sum, [level, count]) => sum + parseInt(level) * count,
      0
    )
    return totalItems > 0 ? weightedSum / totalItems : 3
  }

  const handleEnhancedIndexing = async (materialId: string) => {
    setSelectedMaterial(materialId)

    try {
      // Start basic indexing
      await startIndexing(materialId)

      // Wait for basic indexing to complete (simplified)
      await new Promise(resolve => setTimeout(resolve, 2000))

      // Enhance with Context7
      const baseAnalysis: ContentAnalysisResult = {
        material_id: materialId,
        summary: 'Material content analysis...',
        key_concepts: ['AI', 'Machine Learning', 'Data Processing'],
        difficulty_distribution: { '1': 2, '2': 3, '3': 5, '4': 2, '5': 1 },
        content_types: { 'text': 10, 'heading': 3, 'list': 2 },
        estimated_study_time: 120,
        prerequisite_concepts: ['Basic Programming', 'Mathematics'],
        learning_objectives: ['Understand AI concepts', 'Implement ML models']
      }

      const enhancedResult = await enhanceWithContext7(materialId, baseAnalysis)

      if (onIndexingComplete) {
        onIndexingComplete(materialId, enhancedResult)
      }

    } catch (error) {
      console.error('Enhanced indexing failed:', error)
    } finally {
      setSelectedMaterial(null)
    }
  }

  const renderContext7Insights = () => {
    if (!enhancedAnalysis) return null

    return (
      <div className="space-y-6">
        {/* Context7 Insights Header */}
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl">
              <Cpu className="h-6 w-6 text-white" />
            </div>
            <div>
              <h4 className="font-semibold text-lg text-gray-900">Context7 Insights</h4>
              <p className="text-sm text-gray-600">Analisi potenziata con documentazione in tempo reale</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-purple-50 rounded-xl border border-purple-200">
              <div className="text-2xl font-bold text-purple-600">
                {enhancedAnalysis.context7Insights.latestBestPractices.length}
              </div>
              <p className="text-xs text-gray-600">Best Practices</p>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-xl border border-blue-200">
              <div className="text-2xl font-bold text-blue-600">
                {enhancedAnalysis.context7Insights.codeExamples.length}
              </div>
              <p className="text-xs text-gray-600">Esempi di Codice</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-xl border border-green-200">
              <div className="text-2xl font-bold text-green-600">
                {enhancedAnalysis.context7Insights.currentTrends.length}
              </div>
              <p className="text-xs text-gray-600">Trend Attuali</p>
            </div>
          </div>
        </div>

        {/* Latest Best Practices */}
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <h5 className="font-semibold text-gray-900 mb-4 flex items-center">
            <TrendingUp className="h-5 w-5 mr-2 text-purple-600" />
            Best Practices Aggiornate
          </h5>
          <div className="space-y-3">
            {enhancedAnalysis.context7Insights.latestBestPractices.map((practice, index) => (
              <div key={index} className="flex items-start space-x-3 p-3 bg-purple-50 rounded-lg border border-purple-200">
                <CheckCircle className="h-5 w-5 text-purple-600 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-purple-800">{practice}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Code Examples */}
        {context7Config.includeCodeExamples && (
          <div className="glass rounded-2xl p-6 border border-gray-200/50">
            <h5 className="font-semibold text-gray-900 mb-4 flex items-center">
              <FileText className="h-5 w-5 mr-2 text-blue-600" />
              Esempi di Codice Contestuali
            </h5>
            <div className="space-y-4">
              {enhancedAnalysis.context7Insights.codeExamples.map((example, index) => (
                <div key={index} className="p-4 bg-gray-50 rounded-xl border border-gray-200">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <span className="badge badge-primary">{example.framework}</span>
                      <span className="text-sm text-gray-500">{example.language}</span>
                      <div className="flex items-center space-x-1">
                        <Target className="h-3 w-3 text-gray-400" />
                        <span className="text-xs text-gray-500">Livello {example.difficulty}/5</span>
                      </div>
                    </div>
                  </div>
                  <p className="text-sm text-gray-700 mb-3">{example.description}</p>
                  <div className="bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm overflow-x-auto">
                    <pre>{example.snippet}</pre>
                  </div>
                  <div className="flex flex-wrap gap-2 mt-3">
                    {example.concepts.map((concept, idx) => (
                      <span key={idx} className="badge badge-secondary text-xs">
                        {concept}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Current Trends */}
        {context7Config.fetchLatestTrends && (
          <div className="glass rounded-2xl p-6 border border-gray-200/50">
            <h5 className="font-semibold text-gray-900 mb-4 flex items-center">
              <Zap className="h-5 w-5 mr-2 text-orange-600" />
              Trend Attuali del Settore
            </h5>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {enhancedAnalysis.context7Insights.currentTrends.map((trend, index) => (
                <div key={index} className="p-3 bg-orange-50 rounded-lg border border-orange-200">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                    <span className="text-sm text-orange-800">{trend}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* AI Recommendations */}
        {context7Config.generateRecommendations && (
          <div className="glass rounded-2xl p-6 border border-gray-200/50">
            <h5 className="font-semibold text-gray-900 mb-4 flex items-center">
              <Brain className="h-5 w-5 mr-2 text-green-600" />
              Raccomandazioni AI Personalizzate
            </h5>
            <div className="space-y-4">
              <div>
                <h6 className="font-medium text-gray-800 mb-2">Percorso di Studio Suggerito</h6>
                <div className="space-y-2">
                  {enhancedAnalysis.aiRecommendations.studyPath.map((step, index) => (
                    <div key={index} className="flex items-center space-x-3 p-2 bg-green-50 rounded-lg">
                      <div className="w-6 h-6 bg-green-600 text-white rounded-full flex items-center justify-center text-xs font-medium">
                        {index + 1}
                      </div>
                      <span className="text-sm text-green-800">{step}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h6 className="font-medium text-gray-800 mb-2">Argomenti Correlati</h6>
                <div className="flex flex-wrap gap-2">
                  {enhancedAnalysis.aiRecommendations.relatedTopics.map((topic, index) => (
                    <span key={index} className="badge badge-success">
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderMaterialList = () => (
    <div className="space-y-6">
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center justify-between mb-6">
          <h4 className="font-semibold text-lg text-gray-900">Materiali del Corso</h4>
          <button
            onClick={() => setIsContext7Active(!isContext7Active)}
            className={`btn ${isContext7Active ? 'btn-primary' : 'btn-secondary'}`}
          >
            <Cpu className="h-4 w-4 mr-2" />
            Context7 {isContext7Active ? 'Attivo' : 'Inattivo'}
          </button>
        </div>

        <div className="space-y-4">
          {materials.map((material) => (
            <div
              key={material.id}
              className={`p-4 rounded-xl border transition-all duration-200 ${
                selectedMaterial === material.id
                  ? 'border-purple-300 bg-purple-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-lg ${
                    material.indexingStatus?.status === 'completed'
                      ? 'bg-green-100 text-green-600'
                      : material.indexingStatus?.status === 'processing'
                      ? 'bg-blue-100 text-blue-600'
                      : 'bg-gray-100 text-gray-600'
                  }`}>
                    <FileText className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">{material.name}</div>
                    <div className="text-sm text-gray-500">
                      {material.type} • {(material.size / 1024 / 1024).toFixed(1)} MB
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {material.indexingStatus && (
                    <span className={`badge text-xs ${
                      material.indexingStatus.status === 'completed' ? 'badge-success' :
                      material.indexingStatus.status === 'processing' ? 'badge-primary' :
                      'badge-secondary'
                    }`}>
                      {material.indexingStatus.status === 'completed' ? 'Indicizzato' :
                       material.indexingStatus.status === 'processing' ? 'In corso' : 'Da indicizzare'}
                    </span>
                  )}
                  <button
                    onClick={() => handleEnhancedIndexing(material.id)}
                    disabled={selectedMaterial === material.id || isIndexing}
                    className="btn btn-primary btn-sm"
                  >
                    {selectedMaterial === material.id ? (
                      <RefreshCw className="h-4 w-4 animate-spin" />
                    ) : (
                      <>
                        <ArrowSync className="h-4 w-4 mr-2" />
                        Indicizzazione AI
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Progress Bar for Context7 Enhancement */}
              {selectedMaterial === material.id && isContext7Active && (
                <div className="mt-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-700">Enhancement Context7</span>
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
          ))}
        </div>
      </div>

      {/* Context7 Configuration */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center space-x-3 mb-4">
          <Settings className="h-5 w-5 text-gray-600" />
          <h4 className="font-semibold text-gray-900">Configurazione Context7</h4>
        </div>
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
                 key === 'fetchLatestTrends' ? 'Recupera Trend Attuali' :
                 key === 'analyzeComplexity' ? 'Analisi Complessità' :
                 key === 'generateRecommendations' ? 'Genera Raccomandazioni' :
                 'Analisi Semantica'}
              </span>
            </label>
          ))}
        </div>
      </div>
    </div>
  )

  return (
    <div className="space-y-6">
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl">
            <Cpu className="h-6 w-6 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-lg text-gray-900">
              Enhanced Content Indexer
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Indicizzazione potenziata con Context7 MCP per documentazione in tempo reale
            </p>
          </div>
        </div>

        {/* Status Indicator */}
        {(isIndexing || isContext7Active) && (
          <div className="mb-6 p-4 bg-purple-50 rounded-xl border border-purple-200">
            <div className="flex items-center space-x-3">
              <RefreshCw className="h-5 w-5 animate-spin text-purple-600" />
              <span className="text-purple-800">
                {isIndexing && isContext7Active
                  ? 'Indicizzazione base e enhancement Context7 in corso...'
                  : isIndexing
                  ? 'Indicizzazione base in corso...'
                  : 'Enhancement Context7 in corso...'}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Render Material List or Context7 Insights */}
      {enhancedAnalysis ? renderContext7Insights() : renderMaterialList()}
    </div>
  )
}