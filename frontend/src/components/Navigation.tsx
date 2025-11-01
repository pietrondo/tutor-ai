'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { BookOpen, Brain, BarChart3, Home, Settings, Sparkles, Timer } from 'lucide-react'

export function Navigation() {
  const pathname = usePathname()

  const navigation = [
    { name: 'Home', href: '/', icon: Home, description: 'Dashboard principale' },
    { name: 'Corsi', href: '/courses', icon: BookOpen, description: 'Gestisci i tuoi corsi' },
    { name: 'Chat Tutor', href: '/chat', icon: Brain, description: 'Chatta con l\'AI tutor' },
    { name: 'Timer', href: '/timer', icon: Timer, description: 'Timer di studio Pomodoro' },
    { name: 'Progressi', href: '/progress', icon: BarChart3, description: 'Traccia i tuoi progressi' },
    { name: 'Impostazioni', href: '/settings', icon: Settings, description: 'Configura l\'app' },
  ]

  return (
    <nav className="glass sticky top-0 z-50 backdrop-blur-xl border-b border-gray-200/50">
      <div className="container-responsive">
        <div className="flex justify-between items-center h-16 lg:h-20">
          <div className="flex items-center space-x-6 lg:space-x-8">
            <Link href="/" className="flex items-center space-x-3 group hover-lift">
              <div className="relative">
                <div className="w-10 h-10 lg:w-12 lg:h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg group-hover:shadow-xl transition-all duration-300">
                  <Brain className="h-6 w-6 lg:h-7 lg:w-7 text-white" />
                </div>
                <Sparkles className="absolute -top-1 -right-1 h-3 w-3 text-yellow-500 animate-pulse" />
              </div>
              <div>
                <span className="text-xl lg:text-2xl font-bold text-gradient">Tutor AI</span>
                <p className="hidden lg:block text-xs text-gray-500 mt-0.5">Studio Intelligente</p>
              </div>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden lg:flex items-center space-x-1">
              {navigation.map((item) => {
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`group relative flex flex-col items-center px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                      isActive
                        ? 'bg-gradient-to-r from-blue-500/10 to-purple-500/10 text-blue-700 border border-blue-200/50'
                        : 'text-gray-600 hover:text-blue-700 hover:bg-blue-50/50'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <item.icon className={`h-4 w-4 transition-transform duration-200 ${isActive ? 'scale-110' : 'group-hover:scale-110'}`} />
                      <span>{item.name}</span>
                    </div>
                    {isActive && (
                      <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-1 h-1 bg-blue-600 rounded-full"></div>
                    )}
                  </Link>
                )
              })}
            </div>
          </div>

          {/* Right Section */}
          <div className="flex items-center space-x-4">
            {/* Status Badge - Desktop */}
            <div className="hidden lg:flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-full hover-lift">
              <div className="relative">
                <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                <div className="absolute inset-0 h-2 w-2 bg-green-500 rounded-full animate-ping"></div>
              </div>
              <span className="text-sm font-medium text-green-700">
                AI Tutor Online
              </span>
            </div>

            {/* Mobile Menu Button */}
            <div className="lg:hidden">
              <button className="p-2 rounded-lg hover:bg-gray-100 transition-colors">
                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation */}
        <div className="lg:hidden border-t border-gray-200/50 py-4">
          <div className="grid grid-cols-2 gap-2">
            {navigation.map((item) => {
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex flex-col items-center p-3 rounded-xl transition-all duration-200 ${
                    isActive
                      ? 'bg-gradient-to-r from-blue-500/10 to-purple-500/10 text-blue-700 border border-blue-200/50'
                      : 'text-gray-600 hover:text-blue-700 hover:bg-blue-50/50'
                  }`}
                >
                  <item.icon className={`h-5 w-5 mb-1 ${isActive ? 'scale-110' : ''}`} />
                  <span className="text-xs font-medium">{item.name}</span>
                </Link>
              )
            })}
          </div>
        </div>
      </div>
    </nav>
  )
}