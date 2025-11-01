import './globals.css'
import { Inter } from 'next/font/google'
import { Navigation } from '@/components/Navigation'

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
    'Ollama education',
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
  children: React.ReactNode
}) {
  return (
    <html lang="it" className="scroll-smooth">
      <body className={`${inter.className} antialiased`}>
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
          <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-5"></div>
          <div className="relative">
            <Navigation />
            <main className="container-responsive py-6 sm:py-8 lg:py-12">
              <div className="fade-in">
                {children}
              </div>
            </main>
            <footer className="border-t border-gray-200/50 bg-white/30 backdrop-blur-sm">
              <div className="container-responsive py-8">
                <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
                  <div className="text-center md:text-left">
                    <h3 className="text-lg font-semibold text-gradient">Tutor AI</h3>
                    <p className="text-sm text-gray-600 mt-1">La tua piattaforma di studio intelligente</p>
                  </div>
                  <div className="flex items-center space-x-6">
                    <span className="text-xs text-gray-500">© 2024 Tutor AI</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                      <span className="text-xs text-gray-600">System Online</span>
                    </div>
                  </div>
                </div>
              </div>
            </footer>
          </div>
        </div>
      </body>
    </html>
  )
}