'use client'

import { useState, useEffect } from 'react'
import {
  TrendingUp,
  TrendingDown,
  Brain,
  Target,
  Clock,
  Award,
  BarChart3,
  Calendar,
  Activity,
  Zap,
  CheckCircle,
  AlertCircle,
  Globe,
  Cpu,
  Database,
  Users,
  Eye,
  Lightbulb,
  ArrowUpDown,
  Settings
} from 'lucide-react'

interface EnhancedAnalyticsDashboardProps {
  userId: string
  courseId: string
  timeRange?: '7d' | '30d' | '90d' | 'all'
}

interface Context7Analytics {
  industryBenchmarks: {
    averageMastery: number
    averageStudyTime: number
    popularConcepts: string[]
    emergingTrends: string[]
  }
  globalInsights: {
    totalActiveUsers: number
    totalConceptsMastered: number
    averageCompletionTime: number
    successRate: number
  }
  predictiveAnalytics: {
    masteryProjection: number[]
    difficultyRecommendations: Record<string, number>
    optimalStudySchedule: string[]
    riskFactors: string[]
  }
  competitiveAnalysis: {
    percentileRank: number
    strengthAreas: string[]
    improvementAreas: string[]
    peerComparison: PeerComparison
  }
}

interface PeerComparison {
  betterThan: number
  sameAs: number
  worseThan: number
  averageScore: number
  yourScore: number
}

interface EnhancedAnalyticsData {
  userProgress: any
  learningEfficiency: number
  engagementMetrics: {
    dailyActiveTime: number
    weeklyStreak: number
    sessionQuality: number
    focusScore: number
  }
  knowledgeGaps: {
    criticalGaps: string[]
    recommendedReviews: string[]
    confidenceLevels: Record<string, number>
  }
  context7Insights: Context7Analytics
  realTimeMetrics: {
    currentSessionTime: number
    conceptsExplored: number
    questionsAttempted: number
    accuracyRate: number
  }
}

export function EnhancedAnalyticsDashboard({
  userId,
  courseId,
  timeRange = '30d'
}: EnhancedAnalyticsDashboardProps) {
  const [analyticsData, setAnalyticsData] = useState<EnhancedAnalyticsData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedView, setSelectedView] = useState<'overview' | 'context7' | 'predictions' | 'competitive'>('overview')
  const [showRealTime, setShowRealTime] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(true)

  useEffect(() => {
    loadEnhancedAnalytics()

    if (autoRefresh) {
      const interval = setInterval(() => {
        loadEnhancedAnalytics()
      }, 30000) // Refresh every 30 seconds

      return () => clearInterval(interval)
    }
  }, [userId, courseId, timeRange, autoRefresh])

  const loadEnhancedAnalytics = async () => {
    try {
      setIsLoading(true)
      setError(null)

      // Simulate API call for enhanced analytics data
      const response = await fetch(
        `/api/users/${userId}/enhanced-analytics?courseId=${courseId}&timeRange=${timeRange}`
      )

      if (!response.ok) {
        throw new Error('Failed to load enhanced analytics')
      }

      const data = await response.json()

      // Enhance with Context7 data
      const enhancedData = await enhanceWithContext7(data)
      setAnalyticsData(enhancedData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics')
      console.error('Error loading enhanced analytics:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const enhanceWithContext7 = async (baseData: any): Promise<EnhancedAnalyticsData> => {
    // Simulate Context7 API calls for industry benchmarks and insights
    const context7Insights: Context7Analytics = {
      industryBenchmarks: {
        averageMastery: 0.72,
        averageStudyTime: 180, // minutes per week
        popularConcepts: ['React Hooks', 'TypeScript', 'State Management', 'API Integration'],
        emergingTrends: ['AI Integration', 'Serverless', 'Edge Computing', 'WebAssembly']
      },
      globalInsights: {
        totalActiveUsers: 15420,
        totalConceptsMastered: 89347,
        averageCompletionTime: 45, // days
        successRate: 0.78
      },
      predictiveAnalytics: {
        masteryProjection: [0.65, 0.71, 0.76, 0.82, 0.87],
        difficultyRecommendations: {
          'React Basics': 0.8,
          'Advanced State': 1.2,
          'Performance': 1.1,
          'Testing': 0.9
        },
        optimalStudySchedule: ['Morning: Theory', 'Afternoon: Practice', 'Evening: Review'],
        riskFactors: ['Inconsistent schedule', 'Limited practice time', 'Concept gaps in prerequisites']
      },
      competitiveAnalysis: {
        percentileRank: 73,
        strengthAreas: ['Problem Solving', 'Code Quality', 'Learning Speed'],
        improvementAreas: ['Documentation', 'Testing', 'Performance Optimization'],
        peerComparison: {
          betterThan: 73,
          sameAs: 15,
          worseThan: 12,
          averageScore: 68,
          yourScore: 75
        }
      }
    }

    return {
      userProgress: baseData.userProgress || {},
      learningEfficiency: 0.85,
      engagementMetrics: {
        dailyActiveTime: 145,
        weeklyStreak: 12,
        sessionQuality: 0.88,
        focusScore: 0.92
      },
      knowledgeGaps: {
        criticalGaps: ['Advanced Testing Patterns', 'Performance Optimization'],
        recommendedReviews: ['React Hooks Deep Dive', 'State Management Best Practices'],
        confidenceLevels: {
          'React Basics': 0.9,
          'TypeScript': 0.75,
          'State Management': 0.6,
          'Testing': 0.4
        }
      },
      context7Insights,
      realTimeMetrics: {
        currentSessionTime: 45,
        conceptsExplored: 3,
        questionsAttempted: 8,
        accuracyRate: 0.87
      }
    }
  }

  const renderOverview = () => {
    if (!analyticsData) return null

    const { userProgress, learningEfficiency, engagementMetrics, realTimeMetrics } = analyticsData

    return (
      <div className="space-y-6">
        {/* Key Metrics with Context7 Enhancement */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="glass rounded-xl p-4 border border-gray-200/50">
            <div className="flex items-center justify-between mb-2">
              <Brain className="h-5 w-5 text-purple-600" />
              <span className="text-sm text-green-600 font-medium">
                +{Math.round(learningEfficiency * 100)}%
              </span>
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {Math.round(learningEfficiency * 100)}%
            </div>
            <p className="text-xs text-gray-500">Learning Efficiency</p>
          </div>

          <div className="glass rounded-xl p-4 border border-gray-200/50">
            <div className="flex items-center justify-between mb-2">
              <Activity className="h-5 w-5 text-blue-600" />
              <span className="text-sm text-purple-600 font-medium">
                {engagementMetrics.weeklyStreak} days
              </span>
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {Math.round(engagementMetrics.sessionQuality * 100)}%
            </div>
            <p className="text-xs text-gray-500">Session Quality</p>
          </div>

          <div className="glass rounded-xl p-4 border border-gray-200/50">
            <div className="flex items-center justify-between mb-2">
              <Target className="h-5 w-5 text-green-600" />
              <span className="text-sm text-gray-600">Global</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {Math.round(realTimeMetrics.accuracyRate * 100)}%
            </div>
            <p className="text-xs text-gray-500">Current Accuracy</p>
          </div>

          <div className="glass rounded-xl p-4 border border-gray-200/50">
            <div className="flex items-center justify-between mb-2">
              <Clock className="h-5 w-5 text-orange-600" />
              <span className="text-sm text-gray-600">Today</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {realTimeMetrics.currentSessionTime}m
            </div>
            <p className="text-xs text-gray-500">Session Time</p>
          </div>
        </div>

        {/* Real-time Learning Activity */}
        {showRealTime && (
          <div className="glass rounded-2xl p-6 border border-gray-200/50">
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-semibold text-gray-900 flex items-center">
                <Eye className="h-5 w-5 mr-2 text-blue-600" />
                Real-time Learning Activity
              </h4>
              <div className="flex items-center space-x-2 text-sm text-green-600">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span>Live</span>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-xl">
                <div className="text-2xl font-bold text-blue-600">
                  {realTimeMetrics.conceptsExplored}
                </div>
                <p className="text-xs text-gray-600">Concepts Explored</p>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-xl">
                <div className="text-2xl font-bold text-green-600">
                  {realTimeMetrics.questionsAttempted}
                </div>
                <p className="text-xs text-gray-600">Questions Attempted</p>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-xl">
                <div className="text-2xl font-bold text-purple-600">
                  {Math.round(realTimeMetrics.accuracyRate * 100)}%
                </div>
                <p className="text-xs text-gray-600">Accuracy Rate</p>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-xl">
                <div className="text-2xl font-bold text-orange-600">
                  {Math.round(engagementMetrics.focusScore * 100)}%
                </div>
                <p className="text-xs text-gray-600">Focus Score</p>
              </div>
            </div>
          </div>
        )}

        {/* Knowledge Gaps Analysis */}
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <h4 className="font-semibold text-gray-900 mb-4">Knowledge Gaps Analysis</h4>
          <div className="space-y-4">
            {/* Critical Gaps */}
            <div>
              <h5 className="text-sm font-medium text-red-800 mb-2">Critical Gaps Requiring Attention</h5>
              <div className="space-y-2">
                {analyticsData.knowledgeGaps.criticalGaps.map((gap, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-red-50 rounded-lg border border-red-200">
                    <div className="flex items-center space-x-3">
                      <AlertCircle className="h-5 w-5 text-red-600" />
                      <span className="text-sm text-red-800">{gap}</span>
                    </div>
                    <button className="btn btn-primary btn-sm">Review Now</button>
                  </div>
                ))}
              </div>
            </div>

            {/* Confidence Levels */}
            <div>
              <h5 className="text-sm font-medium text-gray-800 mb-2">Confidence Levels by Concept</h5>
              <div className="space-y-3">
                {Object.entries(analyticsData.knowledgeGaps.confidenceLevels).map(([concept, level]) => (
                  <div key={concept} className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">{concept}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full transition-all duration-500 ${
                            level >= 0.8 ? 'bg-green-500' :
                            level >= 0.6 ? 'bg-blue-500' :
                            level >= 0.4 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${level * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-600 w-10">
                        {Math.round(level * 100)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const renderContext7Insights = () => {
    if (!analyticsData) return null

    const { context7Insights } = analyticsData

    return (
      <div className="space-y-6">
        {/* Industry Benchmarks */}
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <div className="flex items-center space-x-3 mb-4">
            <Globe className="h-5 w-5 text-purple-600" />
            <h4 className="font-semibold text-gray-900">Industry Benchmarks</h4>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="text-center p-4 bg-purple-50 rounded-xl">
              <div className="text-2xl font-bold text-purple-600">
                {Math.round(context7Insights.industryBenchmarks.averageMastery * 100)}%
              </div>
              <p className="text-xs text-gray-600">Industry Average Mastery</p>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-xl">
              <div className="text-2xl font-bold text-blue-600">
                {Math.round(context7Insights.industryBenchmarks.averageStudyTime / 60)}h
              </div>
              <p className="text-xs text-gray-600">Avg Weekly Study Time</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-xl">
              <div className="text-2xl font-bold text-green-600">
                {context7Insights.industryBenchmarks.popularConcepts.length}
              </div>
              <p className="text-xs text-gray-600">Trending Concepts</p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <h5 className="text-sm font-medium text-gray-800 mb-2">Most Popular Concepts Industry-Wide</h5>
              <div className="flex flex-wrap gap-2">
                {context7Insights.industryBenchmarks.popularConcepts.map((concept, index) => (
                  <span key={index} className="badge badge-primary">
                    {concept}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <h5 className="text-sm font-medium text-gray-800 mb-2">Emerging Trends</h5>
              <div className="flex flex-wrap gap-2">
                {context7Insights.industryBenchmarks.emergingTrends.map((trend, index) => (
                  <span key={index} className="badge badge-success">
                    <TrendingUp className="h-3 w-3 mr-1" />
                    {trend}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Global Insights */}
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <div className="flex items-center space-x-3 mb-4">
            <Database className="h-5 w-5 text-blue-600" />
            <h4 className="font-semibold text-gray-900">Global Learning Insights</h4>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-xl">
              <div className="text-2xl font-bold text-gray-900">
                {context7Insights.globalInsights.totalActiveUsers.toLocaleString()}
              </div>
              <p className="text-xs text-gray-600">Active Learners</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-xl">
              <div className="text-2xl font-bold text-gray-900">
                {context7Insights.globalInsights.totalConceptsMastered.toLocaleString()}
              </div>
              <p className="text-xs text-gray-600">Concepts Mastered</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-xl">
              <div className="text-2xl font-bold text-gray-900">
                {context7Insights.globalInsights.averageCompletionTime}d
              </div>
              <p className="text-xs text-gray-600">Avg Completion</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-xl">
              <div className="text-2xl font-bold text-gray-900">
                {Math.round(context7Insights.globalInsights.successRate * 100)}%
              </div>
              <p className="text-xs text-gray-600">Success Rate</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const renderPredictiveAnalytics = () => {
    if (!analyticsData) return null

    const { predictiveAnalytics } = analyticsData.context7Insights

    return (
      <div className="space-y-6">
        {/* Mastery Projection */}
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <div className="flex items-center space-x-3 mb-4">
            <TrendingUp className="h-5 w-5 text-green-600" />
            <h4 className="font-semibold text-gray-900">Mastery Projection</h4>
          </div>

          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-600">Projected mastery over next 5 assessments</span>
              <span className="text-sm text-green-600 font-medium">
                +{Math.round((predictiveAnalytics.masteryProjection[4] - predictiveAnalytics.masteryProjection[0]) * 100)}%
              </span>
            </div>
            <div className="flex items-end space-x-2 h-32">
              {predictiveAnalytics.masteryProjection.map((projection, index) => (
                <div key={index} className="flex-1 flex flex-col items-center">
                  <div
                    className="w-full bg-gradient-to-t from-blue-500 to-green-500 rounded-t"
                    style={{ height: `${projection * 100}%` }}
                  />
                  <span className="text-xs text-gray-500 mt-1">T{index + 1}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Difficulty Recommendations */}
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <h4 className="font-semibold text-gray-900 mb-4">Adaptive Difficulty Recommendations</h4>
          <div className="space-y-3">
            {Object.entries(predictiveAnalytics.difficultyRecommendations).map(([concept, adjustment]) => (
              <div key={concept} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-900">{concept}</span>
                <div className="flex items-center space-x-2">
                  {adjustment > 1 ? (
                    <span className="text-sm text-red-600">
                      <TrendingUp className="h-4 w-4 inline mr-1" />
                      Increase by {Math.round((adjustment - 1) * 100)}%
                    </span>
                  ) : adjustment < 1 ? (
                    <span className="text-sm text-green-600">
                      <TrendingDown className="h-4 w-4 inline mr-1" />
                      Decrease by {Math.round((1 - adjustment) * 100)}%
                    </span>
                  ) : (
                    <span className="text-sm text-gray-600">
                      <Activity className="h-4 w-4 inline mr-1" />
                      Maintain current level
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Optimal Study Schedule */}
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <div className="flex items-center space-x-3 mb-4">
            <Clock className="h-5 w-5 text-purple-600" />
            <h4 className="font-semibold text-gray-900">Optimal Study Schedule</h4>
          </div>
          <div className="space-y-2">
            {predictiveAnalytics.optimalStudySchedule.map((schedule, index) => (
              <div key={index} className="flex items-center space-x-3 p-3 bg-purple-50 rounded-lg">
                <CheckCircle className="h-5 w-5 text-purple-600" />
                <span className="text-sm text-purple-800">{schedule}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Risk Factors */}
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <div className="flex items-center space-x-3 mb-4">
            <AlertCircle className="h-5 w-5 text-orange-600" />
            <h4 className="font-semibold text-gray-900">Risk Factors & Mitigation</h4>
          </div>
          <div className="space-y-3">
            {predictiveAnalytics.riskFactors.map((risk, index) => (
              <div key={index} className="flex items-start space-x-3 p-3 bg-orange-50 rounded-lg">
                <AlertCircle className="h-5 w-5 text-orange-600 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-sm text-orange-800 font-medium">{risk}</div>
                  <div className="text-xs text-orange-700 mt-1">
                    {index === 0 && 'Consider setting fixed study times and reminders'}
                    {index === 1 && 'Start with 15-minute focused sessions and build up'}
                    {index === 2 && 'Review prerequisite concepts before advancing'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const renderCompetitiveAnalysis = () => {
    if (!analyticsData) return null

    const { competitiveAnalysis } = analyticsData.context7Insights

    return (
      <div className="space-y-6">
        {/* Percentile Rank */}
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <div className="flex items-center space-x-3 mb-4">
            <Award className="h-5 w-5 text-yellow-600" />
            <h4 className="font-semibold text-gray-900">Your Performance Ranking</h4>
          </div>

          <div className="text-center mb-6">
            <div className="text-6xl font-bold text-yellow-600 mb-2">
              {competitiveAnalysis.percentileRank}
            </div>
            <p className="text-lg text-gray-600">Percentile Rank</p>
            <p className="text-sm text-gray-500">You're performing better than {competitiveAnalysis.percentileRank}% of learners</p>
          </div>

          {/* Visual Percentile Indicator */}
          <div className="relative h-8 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="absolute inset-y-0 left-0 bg-gradient-to-r from-red-500 via-yellow-500 to-green-500"
              style={{ width: `${competitiveAnalysis.percentileRank}%` }}
            />
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-sm font-medium text-gray-800 bg-white px-2 py-1 rounded">
                Top {100 - competitiveAnalysis.percentileRank}%
              </span>
            </div>
          </div>
        </div>

        {/* Peer Comparison */}
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <div className="flex items-center space-x-3 mb-4">
            <Users className="h-5 w-5 text-blue-600" />
            <h4 className="font-semibold text-gray-900">Peer Comparison</h4>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="text-center p-4 bg-green-50 rounded-xl">
              <div className="text-2xl font-bold text-green-600">
                {competitiveAnalysis.peerComparison.betterThan}%
              </div>
              <p className="text-sm text-gray-600">You Score Better</p>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-xl">
              <div className="text-2xl font-bold text-yellow-600">
                {competitiveAnalysis.peerComparison.sameAs}%
              </div>
              <p className="text-sm text-gray-600">Same Performance</p>
            </div>
            <div className="text-center p-4 bg-red-50 rounded-xl">
              <div className="text-2xl font-bold text-red-600">
                {competitiveAnalysis.peerComparison.worseThan}%
              </div>
              <p className="text-sm text-gray-600">Room to Improve</p>
            </div>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <span className="text-sm text-gray-600">Average Peer Score</span>
            <span className="text-lg font-bold text-gray-900">
              {competitiveAnalysis.peerComparison.averageScore}%
            </span>
          </div>
          <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg border border-blue-200">
            <span className="text-sm text-blue-800 font-medium">Your Score</span>
            <span className="text-lg font-bold text-blue-600">
              {competitiveAnalysis.peerComparison.yourScore}%
            </span>
          </div>
        </div>

        {/* Strength and Improvement Areas */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="glass rounded-2xl p-6 border border-gray-200/50">
            <div className="flex items-center space-x-3 mb-4">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <h4 className="font-semibold text-gray-900">Your Strengths</h4>
            </div>
            <div className="space-y-2">
              {competitiveAnalysis.strengthAreas.map((strength, index) => (
                <div key={index} className="flex items-center space-x-2 p-2 bg-green-50 rounded-lg">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <span className="text-sm text-green-800">{strength}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="glass rounded-2xl p-6 border border-gray-200/50">
            <div className="flex items-center space-x-3 mb-4">
              <Lightbulb className="h-5 w-5 text-orange-600" />
              <h4 className="font-semibold text-gray-900">Improvement Areas</h4>
            </div>
            <div className="space-y-2">
              {competitiveAnalysis.improvementAreas.map((area, index) => (
                <div key={index} className="flex items-center space-x-2 p-2 bg-orange-50 rounded-lg">
                  <Lightbulb className="h-4 w-4 text-orange-600" />
                  <span className="text-sm text-orange-800">{area}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="glass rounded-2xl p-8 border border-gray-200/50 text-center">
        <Cpu className="h-8 w-8 text-blue-600 mx-auto mb-4 animate-pulse" />
        <p className="text-gray-600">Loading enhanced analytics with Context7 insights...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="glass rounded-2xl p-8 border border-gray-200/50 text-center">
        <AlertCircle className="h-8 w-8 text-red-600 mx-auto mb-4" />
        <p className="text-red-600">{error}</p>
        <button
          onClick={loadEnhancedAnalytics}
          className="btn btn-primary btn-sm mt-4"
        >
          Retry
        </button>
      </div>
    )
  }

  if (!analyticsData) {
    return null
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl">
              <BarChart3 className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-lg text-gray-900">
                Enhanced Analytics Dashboard
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Advanced insights powered by Context7 MCP and real-time data
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="form-checkbox"
              />
              <span className="text-sm text-gray-700">Auto-refresh</span>
            </label>
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showRealTime}
                onChange={(e) => setShowRealTime(e.target.checked)}
                className="form-checkbox"
              />
              <span className="text-sm text-gray-700">Real-time</span>
            </label>
            <select
              value={timeRange}
              onChange={(e) => setSelectedView(e.target.value as any)}
              className="form-input text-sm"
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
              <option value="all">All time</option>
            </select>
          </div>
        </div>

        {/* Enhanced View Tabs */}
        <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
          {[
            { id: 'overview', label: 'Overview', icon: BarChart3 },
            { id: 'context7', label: 'Context7 Insights', icon: Cpu },
            { id: 'predictions', label: 'Predictions', icon: TrendingUp },
            { id: 'competitive', label: 'Competitive', icon: Award }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedView(tab.id as any)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-all duration-200 ${
                selectedView === tab.id
                  ? 'bg-white text-purple-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <tab.icon className="h-4 w-4" />
              <span className="text-sm font-medium">{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Content Based on Selected View */}
      {selectedView === 'overview' && renderOverview()}
      {selectedView === 'context7' && renderContext7Insights()}
      {selectedView === 'predictions' && renderPredictiveAnalytics()}
      {selectedView === 'competitive' && renderCompetitiveAnalysis()}

      {/* Context7 Attribution */}
      <div className="glass rounded-xl p-4 border border-gray-200/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Cpu className="h-4 w-4 text-purple-600" />
            <span className="text-sm text-gray-600">
              Powered by Context7 MCP for real-time documentation and industry insights
            </span>
          </div>
          {autoRefresh && (
            <div className="flex items-center space-x-2 text-sm text-green-600">
              <ArrowUpDown className="h-4 w-4 animate-spin" />
              <span>Auto-refreshing</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}