import './globals.css'
import type { ReactNode } from 'react'
import { Inter } from 'next/font/google'
import { Navigation } from '@/components/Navigation'
import { ThemeProvider } from '@/contexts/ThemeContext'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: {
    default: 'Tutor-AI - Piattaforma di Studio Intelligente',
    template: '%s | Tutor-AI'
  },
  description: 'Trasforma il tuo studio universitario con l\'AI tutor personalizzato. Carica PDF, chatta con l\'assistente intelligente, traccia progressi e genera quiz automatici.',
  keywords: [
    'tutor AI',
    'studio universitario',
    'apprendimento intelligente',
    'RAG system',
    'chat educativa',
    'quiz automatici',
    'progressi studio',
    'materiale didattico',
    'assistente virtuale',
    'OpenAI tutor',
      'LM Studio learning'
  ],
  authors: [{ name: 'Tutor-AI Team' }],
  creator: 'Tutor-AI',
  publisher: 'Tutor-AI',
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  openGraph: {
    type: 'website',
    locale: 'it_IT',
    url: 'https://tutor-ai.com',
    title: 'Tutor-AI - Piattaforma di Studio Intelligente',
    description: 'Il tuo assistente di studio universitario con AI avanzata, RAG e tracciamento dei progressi.',
    siteName: 'Tutor-AI',
    images: [
      {
        url: '/og-image.svg',
        width: 1200,
        height: 630,
        alt: 'Tutor-AI - Dashboard principale con corsi e statistiche',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Tutor-AI - Studio Intelligente con AI',
    description: 'Trasforma il tuo studio universitario con AI tutor personalizzato e materiali intelligenti.',
    images: ['/og-image.svg'],
    creator: '@tutor_ai',
  },
  icons: {
    icon: [
      { url: '/favicon.ico', sizes: '32x32', type: 'image/x-icon' },
      { url: '/icon.svg', sizes: 'any', type: 'image/svg+xml' },
    ],
    apple: [
      { url: '/maskable-icon.svg', sizes: '512x512', type: 'image/svg+xml' },
    ],
  },
  manifest: '/manifest.json',
  other: {
    'msapplication-TileColor': '#3b82f6',
    'msapplication-config': '/browserconfig.xml',
  },
}

export default function RootLayout({
  children,
}: {
  children: ReactNode
}) {
  return (
    <html lang="it" className="scroll-smooth">
      <body className={`${inter.className} antialiased`} suppressHydrationWarning={true}>
        <ThemeProvider>
          <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-rose-50 relative overflow-hidden dark:from-gray-900 dark:via-blue-900 dark:to-purple-900">
          {/* Animated background elements */}
          <div className="absolute inset-0 overflow-hidden">
            <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-blue-400/10 via-purple-400/10 to-pink-400/10 rounded-full blur-3xl animate-float"></div>
            <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-br from-amber-400/10 via-rose-400/10 to-purple-400/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }}></div>
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-gradient-to-br from-emerald-400/5 via-cyan-400/5 to-blue-400/5 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '4s' }}></div>
          </div>

          <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-5"></div>
          <div className="relative z-10">
            <Navigation />
            <main className="container-responsive py-6 sm:py-8 lg:py-12">
              <div className="fade-in">
                {children}
              </div>
            </main>
            <footer className="border-t border-gray-200/30 bg-white/40 backdrop-blur-sm mt-12">
              <div className="container-responsive py-8">
                <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
                  <div className="text-center md:text-left">
                    <div className="flex items-center space-x-3 mb-2">
                      <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg shadow-lg">
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                        </svg>
                      </div>
                      <h3 className="text-lg font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">Tutor AI</h3>
                    </div>
                    <p className="text-sm text-gray-600">La tua piattaforma di studio intelligente</p>
                  </div>
                  <div className="flex items-center space-x-6">
                    <span className="text-xs text-gray-500">© 2024 Tutor AI</span>
                    <div className="flex items-center space-x-2 px-3 py-1 bg-gradient-to-r from-emerald-50 to-cyan-50 rounded-full border border-emerald-200">
                      <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                      <span className="text-xs font-medium text-emerald-700">System Online</span>
                    </div>
                  </div>
                </div>
              </div>
            </footer>
          </div>
        </div>
      </ThemeProvider>
      </body>
    </html>
  )
}
