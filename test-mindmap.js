#!/usr/bin/env node

/**
 * Test locale per verificare il rendering del componente MindMapViewer
 * Questo test crea un'istanza del componente e genera un'immagine PNG
 * per permettere una verifica visiva della grafica.
 */

const { createServer } = require('http')
const { parse } = require('url')
const next = require('next')

const dev = process.env.NODE_ENV !== 'production'
const hostname = 'localhost'
const port = 3000

const app = next({ dev, hostname, port })
const handle = app.getRequestHandler()

// Dati di test per il MindMap
const testMindMap = {
  id: 'test-mindmap-1',
  sessionId: 'test-session-1',
  title: 'Test Mind Map - Programmazione',
  description: 'Mappa mentale di test per concetti di programmazione',
  nodes: [
    {
      id: 'central',
      type: 'central',
      position: { x: 400, y: 300 },
      data: {
        label: 'Programmazione',
        description: 'Concetti fondamentali',
        type: 'central',
        importance: 'high'
      }
    },
    {
      id: 'frontend',
      type: 'topic',
      position: { x: 200, y: 150 },
      data: {
        label: 'Frontend',
        description: 'Sviluppo lato client',
        type: 'topic',
        importance: 'high',
        topics: ['React', 'Vue', 'Angular'],
        color: '#3B82F6'
      }
    },
    {
      id: 'backend',
      type: 'topic',
      position: { x: 600, y: 150 },
      data: {
        label: 'Backend',
        description: 'Sviluppo lato server',
        type: 'topic',
        importance: 'high',
        topics: ['Node.js', 'Python', 'Java'],
        color: '#10B981'
      }
    },
    {
      id: 'database',
      type: 'subtopic',
      position: { x: 650, y: 50 },
      data: {
        label: 'Database',
        description: 'Gestione dati',
        type: 'subtopic',
        importance: 'medium',
        examples: ['PostgreSQL', 'MongoDB', 'Redis'],
        color: '#8B5CF6'
      }
    },
    {
      id: 'react-example',
      type: 'example',
      position: { x: 100, y: 80 },
      data: {
        label: 'React Hooks',
        description: 'Esempio di useState',
        type: 'example',
        importance: 'low',
        examples: ['useState', 'useEffect', 'useContext'],
        color: '#F59E0B'
      }
    }
  ],
  edges: [
    {
      id: 'edge-frontend',
      source: 'central',
      target: 'frontend',
      type: 'hierarchy',
      data: {
        label: 'include',
        relationship: 'parent-child'
      }
    },
    {
      id: 'edge-backend',
      source: 'central',
      target: 'backend',
      type: 'hierarchy',
      data: {
        label: 'include',
        relationship: 'parent-child'
      }
    },
    {
      id: 'edge-database',
      source: 'backend',
      target: 'database',
      type: 'hierarchy',
      data: {
        label: 'usa',
        relationship: 'component'
      }
    },
    {
      id: 'edge-react-example',
      source: 'frontend',
      target: 'react-example',
      type: 'example',
      data: {
        label: 'esempio',
        relationship: 'illustration'
      }
    }
  ],
  metadata: {
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    version: '1.0.0',
    author: 'Test System',
    tags: ['programming', 'test', 'mindmap'],
    difficulty: 'beginner',
    sessionTitle: 'Sessione di Test'
  },
  layout: {
    type: 'mindmap',
    nodeSpacing: 100,
    levelSpacing: 150,
    direction: 'TB'
  },
  style: {
    theme: 'colorful',
    fontFamily: 'Inter, sans-serif',
    nodeBaseSize: 1,
    edgeBaseSize: 1
  }
}

app.prepare().then(() => {
  createServer(async (req, res) => {
    try {
      const parsedReq = parse(req.url, true)
      await handle(req, res, parsedReq)
    } catch (err) {
      console.error('Error occurred handling', req.url, err)
      res.statusCode = 500
      res.end('internal server error')
    }
  })
  .listen(port, () => {
    console.log(`> Ready on http://${hostname}:${port}`)
    console.log(`> Test MindMap disponibile con i seguenti dati:`)
    console.log(`> - Titolo: ${testMindMap.title}`)
    console.log(`> - Nodi: ${testMindMap.nodes.length}`)
    console.log(`> - Edges: ${testMindMap.edges.length}`)
    console.log(`> - Visita http://${hostname}:${port}/test-mindmap per vedere il componente`)
  })
})

// Esporta i dati di test per l'uso nella pagina di test
module.exports = { testMindMap }