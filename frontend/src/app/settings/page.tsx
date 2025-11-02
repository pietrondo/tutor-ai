'use client'

import { useState, useEffect } from 'react'
import { Settings, Brain, Database, Globe, Shield, Bell, Palette, Save, RefreshCw, Key, Eye, EyeOff, CheckCircle, AlertCircle, Sun, Moon } from 'lucide-react'
import ModelManager from '@/components/ModelManager'
import { RAGManagementPanel } from '@/components/RAGManagementPanel'
import { useTheme } from '@/contexts/ThemeContext'

interface SelectFieldOption {
  value: string
  label: string
}

interface SelectField {
  name: string
  label: string
  type: 'select'
  options: SelectFieldOption[]
}

interface CheckboxField {
  name: string
  label: string
  type: 'checkbox'
}

type FormField = SelectField | CheckboxField

interface SettingsSection {
  title: string
  icon: any
  color: string
  fields: FormField[]
}

export default function SettingsPage() {
  const { theme, setTheme, effectiveTheme } = useTheme()
  const [settings, setSettings] = useState({
    llmProvider: 'openai',
    notifications: true,
    autoSave: true,
    language: 'it',
    apiEndpoint: 'http://localhost:8000'
  })

  const [apiKeys, setApiKeys] = useState({
    openai: '',
    openrouter: '',
    anthropic: ''
  })

  const [showApiKeys, setShowApiKeys] = useState<Record<string, boolean>>({})
  const [testingKey, setTestingKey] = useState<string | null>(null)
  const [keyStatus, setKeyStatus] = useState<Record<string, { valid: boolean; message: string }>>({})

  const [loading, setLoading] = useState(false)
  const [saveStatus, setSaveStatus] = useState('')

  // Test API key function
  const testApiKey = async (provider: string, apiKey: string) => {
    setTestingKey(provider)
    setKeyStatus(prev => ({ ...prev, [provider]: { valid: false, message: 'Test in corso...' } }))

    try {
      let baseUrl = ''
      let headers: Record<string, string> = {
        'Content-Type': 'application/json'
      }

      switch (provider) {
        case 'openai':
          baseUrl = 'https://api.openai.com/v1'
          headers['Authorization'] = `Bearer ${apiKey}`
          break
        case 'openrouter':
          baseUrl = 'https://openrouter.ai/api/v1'
          headers['Authorization'] = `Bearer ${apiKey}`
          headers['HTTP-Referer'] = window.location.origin
          headers['X-Title'] = 'AI Tutor System'
          break
        case 'anthropic':
          baseUrl = 'https://api.anthropic.com/v1'
          headers['x-api-key'] = apiKey
          headers['anthropic-version'] = '2023-06-01'
          break
        default:
          throw new Error('Provider non supportato')
      }

      const response = await fetch(`${baseUrl}/models`, {
        headers,
        signal: AbortSignal.timeout(10000)
      })

      if (response.ok) {
        setKeyStatus(prev => ({
          ...prev,
          [provider]: { valid: true, message: '✅ API Key valida e funzionante!' }
        }))
      } else {
        const errorText = await response.text()
        setKeyStatus(prev => ({
          ...prev,
          [provider]: { valid: false, message: `❌ Errore ${response.status}: ${response.statusText}` }
        }))
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Errore sconosciuto'
      setKeyStatus(prev => ({
        ...prev,
        [provider]: { valid: false, message: `❌ Errore di connessione: ${errorMessage}` }
      }))
    } finally {
      setTestingKey(null)
    }
  }

  const toggleApiKeyVisibility = (provider: string) => {
    setShowApiKeys(prev => ({ ...prev, [provider]: !prev[provider] }))
  }

  const handleSave = async () => {
    setLoading(true)
    setSaveStatus('')

    try {
      // Simulate saving settings
      await new Promise(resolve => setTimeout(resolve, 1000))
      setSaveStatus('Impostazioni salvate con successo!')

      // Clear status after 3 seconds
      setTimeout(() => setSaveStatus(''), 3000)
    } catch (error) {
      setSaveStatus('Errore nel salvataggio delle impostazioni')
    } finally {
      setLoading(false)
    }
  }

  const settingSections: SettingsSection[] = [
    {
      title: 'Preferenze AI',
      icon: Brain,
      color: 'blue',
      fields: [
        {
          name: 'llmProvider',
          label: 'Provider LLM',
          type: 'select',
          options: [
            { value: 'openai', label: 'OpenAI (GPT-4, GPT-4o, etc.)' },
            { value: 'ollama', label: 'Ollama (Locale)' },
            { value: 'lmstudio', label: 'LM Studio (Locale)' },
            { value: 'local', label: 'Locale (Legacy)' }
          ]
        }
      ]
    },
    {
      title: 'Notifiche',
      icon: Bell,
      color: 'yellow',
      fields: [
        {
          name: 'notifications',
          label: 'Abilita notifiche',
          type: 'checkbox'
        },
        {
          name: 'autoSave',
          label: 'Salvataggio automatico',
          type: 'checkbox'
        }
      ]
    },
    {
      title: 'Lingua',
      icon: Globe,
      color: 'green',
      fields: [
        {
          name: 'language',
          label: 'Lingua interfaccia',
          type: 'select',
          options: [
            { value: 'it', label: 'Italiano' },
            { value: 'en', label: 'English' }
          ]
        }
      ]
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 relative overflow-hidden dark:from-gray-900 dark:via-gray-800 dark:to-purple-900">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-blue-400/20 to-purple-400/20 rounded-full blur-3xl animate-float"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-br from-pink-400/20 to-orange-400/20 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }}></div>
      </div>

      <div className="container-responsive py-8 relative z-10">
        {/* Enhanced Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-4 mb-2 group">
            <div className="p-4 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl shadow-xl group-hover:shadow-2xl group-hover:scale-105 transition-all duration-500 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent transform -skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
              <Settings className="h-8 w-8 text-white relative z-10 group-hover:rotate-12 transition-transform duration-300" />
            </div>
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent group-hover:from-blue-600 group-hover:to-purple-600 transition-all duration-500 dark:from-gray-100 dark:to-gray-300 dark:group-hover:from-blue-400 dark:group-hover:to-purple-400">
                Impostazioni
              </h1>
              <p className="text-gray-600 mt-1 text-lg dark:text-gray-400">Personalizza la tua esperienza di apprendimento</p>
            </div>
          </div>
        </div>

        {/* Theme Section */}
        <div className="glass-card rounded-2xl p-6 mb-8 border border-gray-200/50 hover:border-blue-200/50 transition-all duration-500 relative overflow-hidden dark:border-gray-700/50">
          {/* Animated gradient background */}
          <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-pink-500/5 to-blue-500/5 opacity-50 dark:from-purple-500/10 dark:via-pink-500/10 dark:to-blue-500/10"></div>

          {/* Top accent line */}
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-500 via-pink-500 to-blue-500"></div>

          <div className="relative z-10">
            <div className="flex items-center space-x-3 mb-6">
              <div className="p-3 bg-gradient-to-br from-purple-100 to-pink-100 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-110 hover:rotate-12 dark:from-purple-900/50 dark:to-pink-900/50">
                <Palette className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <h3 className="text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent dark:from-gray-100 dark:to-gray-300">
                Aspetto
              </h3>
            </div>

            <div className="space-y-6">
              {/* Theme Toggle with visual preview */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-4 dark:text-gray-300">
                  Tema Interface
                </label>
                <div className="grid grid-cols-3 gap-4">
                  <button
                    onClick={() => setTheme('light')}
                    className={`relative p-4 rounded-xl border-2 transition-all duration-300 ${
                      theme === 'light'
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-400'
                        : 'border-gray-200 hover:border-gray-300 dark:border-gray-700 dark:hover:border-gray-600'
                    }`}
                  >
                    <div className="flex flex-col items-center space-y-2">
                      <Sun className={`h-6 w-6 ${theme === 'light' ? 'text-blue-500' : 'text-gray-400'}`} />
                      <span className={`text-sm font-medium ${theme === 'light' ? 'text-blue-700' : 'text-gray-600 dark:text-gray-400'}`}>
                        Chiaro
                      </span>
                    </div>
                    {theme === 'light' && (
                      <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full border-2 border-white dark:border-gray-900"></div>
                    )}
                  </button>

                  <button
                    onClick={() => setTheme('dark')}
                    className={`relative p-4 rounded-xl border-2 transition-all duration-300 ${
                      theme === 'dark'
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-400'
                        : 'border-gray-200 hover:border-gray-300 dark:border-gray-700 dark:hover:border-gray-600'
                    }`}
                  >
                    <div className="flex flex-col items-center space-y-2">
                      <Moon className={`h-6 w-6 ${theme === 'dark' ? 'text-blue-500' : 'text-gray-400'}`} />
                      <span className={`text-sm font-medium ${theme === 'dark' ? 'text-blue-700 dark:text-blue-300' : 'text-gray-600 dark:text-gray-400'}`}>
                        Scuro
                      </span>
                    </div>
                    {theme === 'dark' && (
                      <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full border-2 border-white dark:border-gray-900"></div>
                    )}
                  </button>

                  <button
                    onClick={() => setTheme('auto')}
                    className={`relative p-4 rounded-xl border-2 transition-all duration-300 ${
                      theme === 'auto'
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-400'
                        : 'border-gray-200 hover:border-gray-300 dark:border-gray-700 dark:hover:border-gray-600'
                    }`}
                  >
                    <div className="flex flex-col items-center space-y-2">
                      <div className="relative">
                        <Sun className={`h-6 w-6 absolute -top-1 -left-1 ${theme === 'auto' ? 'text-blue-500' : 'text-gray-300'}`} />
                        <Moon className={`h-6 w-6 ${theme === 'auto' ? 'text-blue-500' : 'text-gray-400'}`} />
                      </div>
                      <span className={`text-sm font-medium ${theme === 'auto' ? 'text-blue-700 dark:text-blue-300' : 'text-gray-600 dark:text-gray-400'}`}>
                        Auto
                      </span>
                    </div>
                    {theme === 'auto' && (
                      <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full border-2 border-white dark:border-gray-900"></div>
                    )}
                  </button>
                </div>

                <div className="mt-4 p-3 bg-gray-50 rounded-lg dark:bg-gray-800/50">
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {theme === 'auto'
                      ? `Tema automatico: Attualmente ${effectiveTheme === 'dark' ? 'scuro' : 'chiaro'} basato sulle impostazioni di sistema`
                      : `Tema ${theme === 'dark' ? 'scuro' : 'chiaro'} selezionato manualmente`
                    }
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Settings Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {settingSections.map((section) => (
            <div key={section.title} className="glass-card rounded-2xl p-6 border border-gray-200/50 hover:border-blue-200/50 transition-all duration-500 group relative overflow-hidden">
              {/* Animated gradient background */}
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-purple-500/5 to-pink-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>

              {/* Top accent line */}
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-blue-500 to-transparent transform scale-x-0 group-hover:scale-x-100 transition-transform duration-700"></div>

              <div className="relative z-10">
                <div className="flex items-center space-x-3 mb-6">
                  <div className={`p-3 rounded-xl transition-all duration-500 group-hover:scale-110 group-hover:rotate-12 ${
                    section.color === 'blue' ? 'bg-gradient-to-br from-blue-100 to-blue-200 text-blue-600 shadow-lg group-hover:shadow-xl' :
                    section.color === 'purple' ? 'bg-gradient-to-br from-purple-100 to-purple-200 text-purple-600 shadow-lg group-hover:shadow-xl' :
                    section.color === 'yellow' ? 'bg-gradient-to-br from-yellow-100 to-orange-100 text-yellow-600 shadow-lg group-hover:shadow-xl' :
                    'bg-gradient-to-br from-green-100 to-emerald-100 text-green-600 shadow-lg group-hover:shadow-xl'
                  }`}>
                    <section.icon className={`h-5 w-5`} />
                  </div>
                  <h3 className="text-lg font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent group-hover:from-blue-600 group-hover:to-purple-600 transition-all duration-500">
                    {section.title}
                  </h3>
                </div>

              <div className="space-y-4">
                {section.fields.map((field) => (
                  <div key={field.name}>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {field.label}
                    </label>

                    {field.type === 'select' ? (
                      <select
                        value={String(settings[field.name as keyof typeof settings])}
                        onChange={(e) => setSettings(prev => ({
                          ...prev,
                          [field.name]: e.target.value
                        }))}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                      >
                        {field.options?.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    ) : field.type === 'checkbox' ? (
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id={field.name}
                          checked={settings[field.name as keyof typeof settings] as boolean}
                          onChange={(e) => setSettings(prev => ({
                            ...prev,
                            [field.name]: e.target.checked
                          }))}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded transition-all duration-200"
                        />
                        <label htmlFor={field.name} className="ml-2 text-sm text-gray-600">
                          {field.label}
                        </label>
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
              </div>
            </div>
          ))}
        </div>

        {/* Model Manager Section */}
        <div className="glass-card rounded-2xl p-8 mb-8 border border-gray-200/50 hover:border-blue-200/50 transition-all duration-500 relative overflow-hidden">
          {/* Animated gradient background */}
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-purple-500/5 to-pink-500/5 opacity-100"></div>

          {/* Top accent line */}
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500"></div>

          <div className="relative z-10">
            <div className="flex items-center space-x-3 mb-6">
              <div className="p-3 bg-gradient-to-br from-blue-100 to-purple-100 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-110 hover:rotate-12">
                <Brain className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                Gestione Modelli AI
              </h3>
            </div>

            <ModelManager />
          </div>
        </div>

        {/* RAG Management Section */}
        <div className="glass-card rounded-2xl p-6 mb-8 border border-gray-200/50 hover:border-blue-200/50 transition-all duration-500 relative overflow-hidden">
          {/* Animated gradient background */}
          <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 via-emerald-500/5 to-blue-500/5 opacity-50"></div>

          {/* Top accent line */}
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-green-500 via-emerald-500 to-blue-500"></div>

          <div className="relative z-10">
            <div className="flex items-center space-x-3 mb-6">
              <div className="p-3 bg-gradient-to-br from-green-100 to-emerald-100 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-110 hover:rotate-12">
                <Database className="h-6 w-6 text-green-600" />
              </div>
              <h3 className="text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                Gestione RAG
              </h3>
            </div>

            <RAGManagementPanel />
          </div>
        </div>

        {/* API Keys Section (simplified) */}
        <div className="glass-card rounded-2xl p-6 mb-8 border border-gray-200/50 hover:border-blue-200/50 transition-all duration-500 relative overflow-hidden">
          {/* Animated gradient background */}
          <div className="absolute inset-0 bg-gradient-to-br from-yellow-500/5 via-orange-500/5 to-red-500/5 opacity-50"></div>

          {/* Top accent line */}
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-yellow-500 via-orange-500 to-red-500"></div>

          <div className="relative z-10">
            <div className="flex items-center space-x-3 mb-6">
              <div className="p-3 bg-gradient-to-br from-yellow-100 to-orange-100 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-110 hover:rotate-12">
                <Key className="h-6 w-6 text-yellow-600" />
              </div>
              <h3 className="text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                Chiavi API
              </h3>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* OpenAI API Key */}
              <div className="space-y-3">
                <h4 className="font-semibold text-gray-800 flex items-center">
                  <Brain className="h-4 w-4 mr-2 text-blue-600" />
                  OpenAI
                </h4>
                <div className="relative">
                  <input
                    type={showApiKeys.openai ? 'text' : 'password'}
                    value={apiKeys.openai}
                    onChange={(e) => setApiKeys(prev => ({ ...prev, openai: e.target.value }))}
                    placeholder="sk-proj-..."
                    className="w-full px-4 py-3 pr-20 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-300 bg-white/80 backdrop-blur"
                  />
                  <button
                    type="button"
                    onClick={() => toggleApiKeyVisibility('openai')}
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 text-gray-400 hover:text-gray-600 transition-colors duration-200"
                  >
                    {showApiKeys.openai ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                <button
                  onClick={() => testApiKey('openai', apiKeys.openai)}
                  disabled={!apiKeys.openai || testingKey === 'openai'}
                  className="w-full px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg font-medium transition-all duration-300 hover:from-blue-600 hover:to-blue-700 hover:shadow-lg hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                >
                  {testingKey === 'openai' ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      <span>Test...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle className="h-4 w-4" />
                      <span>Test</span>
                    </>
                  )}
                </button>
                {keyStatus.openai && (
                  <div className={`p-3 rounded-lg border text-sm ${
                    keyStatus.openai.valid
                      ? 'bg-green-50 border-green-200 text-green-800'
                      : 'bg-red-50 border-red-200 text-red-800'
                  }`}>
                    {keyStatus.openai.message}
                  </div>
                )}
              </div>

              {/* OpenRouter API Key */}
              <div className="space-y-3">
                <h4 className="font-semibold text-gray-800 flex items-center">
                  <Globe className="h-4 w-4 mr-2 text-purple-600" />
                  OpenRouter
                </h4>
                <div className="relative">
                  <input
                    type={showApiKeys.openrouter ? 'text' : 'password'}
                    value={apiKeys.openrouter}
                    onChange={(e) => setApiKeys(prev => ({ ...prev, openrouter: e.target.value }))}
                    placeholder="sk-or-v1-..."
                    className="w-full px-4 py-3 pr-20 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-300 bg-white/80 backdrop-blur"
                  />
                  <button
                    type="button"
                    onClick={() => toggleApiKeyVisibility('openrouter')}
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 text-gray-400 hover:text-gray-600 transition-colors duration-200"
                  >
                    {showApiKeys.openrouter ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                <button
                  onClick={() => testApiKey('openrouter', apiKeys.openrouter)}
                  disabled={!apiKeys.openrouter || testingKey === 'openrouter'}
                  className="w-full px-4 py-2 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-lg font-medium transition-all duration-300 hover:from-purple-600 hover:to-purple-700 hover:shadow-lg hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                >
                  {testingKey === 'openrouter' ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      <span>Test...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle className="h-4 w-4" />
                      <span>Test</span>
                    </>
                  )}
                </button>
                {keyStatus.openrouter && (
                  <div className={`p-3 rounded-lg border text-sm ${
                    keyStatus.openrouter.valid
                      ? 'bg-green-50 border-green-200 text-green-800'
                      : 'bg-red-50 border-red-200 text-red-800'
                  }`}>
                    {keyStatus.openrouter.message}
                  </div>
                )}
              </div>

              {/* Anthropic API Key */}
              <div className="space-y-3">
                <h4 className="font-semibold text-gray-800 flex items-center">
                  <AlertCircle className="h-4 w-4 mr-2 text-orange-600" />
                  Anthropic
                </h4>
                <div className="relative">
                  <input
                    type={showApiKeys.anthropic ? 'text' : 'password'}
                    value={apiKeys.anthropic}
                    onChange={(e) => setApiKeys(prev => ({ ...prev, anthropic: e.target.value }))}
                    placeholder="sk-ant-..."
                    className="w-full px-4 py-3 pr-20 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all duration-300 bg-white/80 backdrop-blur"
                  />
                  <button
                    type="button"
                    onClick={() => toggleApiKeyVisibility('anthropic')}
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 text-gray-400 hover:text-gray-600 transition-colors duration-200"
                  >
                    {showApiKeys.anthropic ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                <button
                  onClick={() => testApiKey('anthropic', apiKeys.anthropic)}
                  disabled={!apiKeys.anthropic || testingKey === 'anthropic'}
                  className="w-full px-4 py-2 bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-lg font-medium transition-all duration-300 hover:from-orange-600 hover:to-orange-700 hover:shadow-lg hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                >
                  {testingKey === 'anthropic' ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      <span>Test...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle className="h-4 w-4" />
                      <span>Test</span>
                    </>
                  )}
                </button>
                {keyStatus.anthropic && (
                  <div className={`p-3 rounded-lg border text-sm ${
                    keyStatus.anthropic.valid
                      ? 'bg-green-50 border-green-200 text-green-800'
                      : 'bg-red-50 border-red-200 text-red-800'
                  }`}>
                    {keyStatus.anthropic.message}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Advanced Settings */}
        <div className="glass-card rounded-2xl p-6 mb-8 border border-gray-200/50 hover:border-blue-200/50 transition-all duration-500 group relative overflow-hidden">
          {/* Animated gradient background */}
          <div className="absolute inset-0 bg-gradient-to-br from-red-500/5 via-pink-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>

          {/* Top accent line */}
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-red-500 via-pink-500 to-purple-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-700"></div>

          <div className="relative z-10">
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-2 bg-red-100 rounded-lg">
              <Shield className="h-5 w-5 text-red-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Impostazioni Avanzate</h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Endpoint API
              </label>
              <input
                type="url"
                value={settings.apiEndpoint}
                onChange={(e) => setSettings(prev => ({
                  ...prev,
                  apiEndpoint: e.target.value
                }))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                placeholder="http://localhost:8000"
              />
            </div>
          </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {saveStatus && (
              <div className={`text-sm font-medium ${
                saveStatus.includes('success') ? 'text-green-600' : 'text-red-600'
              }`}>
                {saveStatus}
              </div>
            )}
          </div>

          <div className="flex items-center space-x-3">
            <button className="px-6 py-3 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-all duration-200 hover-lift flex items-center space-x-2">
              <RefreshCw className="h-4 w-4" />
              <span>Ripristina</span>
            </button>

            <button
              onClick={handleSave}
              disabled={loading}
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg font-medium transition-all duration-200 hover-lift flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <Save className="h-4 w-4" />
              )}
              <span>{loading ? 'Salvataggio...' : 'Salva Impostazioni'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}