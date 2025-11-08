/**
 * Servizio Unificato Mappe Mentali
 * Gestisce generazione, cache e condivisione di mappe tra chat e pagina dedicata
 */

import { StudyMindmap, StudyMindmapNode } from '@/types/mindmap'

const CACHE_KEY_PREFIX = 'mindmap_'
const CACHE_VERSION = '1.0'
const CACHE_EXPIRY_HOURS = 24

export interface MindmapCache {
  data: StudyMindmap
  timestamp: number
  courseId: string
  bookId?: string
  version: string
}

export interface MindmapGenerateRequest {
  courseId: string
  bookId?: string
  topic?: string
  focusAreas?: string[]
  forceRegenerate?: boolean
}

export interface MindmapStorage {
  id: string
  courseId: string
  bookId?: string
  title: string
  mindmap: StudyMindmap
  markdown?: string
  references?: string[]
  sources?: any[]
  createdAt: string
  lastAccessed: string
}

class MindmapService {
  private cache: Map<string, MindmapCache> = new Map()

  constructor() {
    this.loadCacheFromStorage()
    // Pulizia cache scaduti
    this.cleanExpiredCache()
  }

  /**
   * Genera o recupera una mappa mentale dalla cache
   */
  async getMindmap(request: MindmapGenerateRequest): Promise<{
    mindmap: StudyMindmap | null
    fromCache: boolean
    error?: string
  }> {
    const cacheKey = this.buildCacheKey(request.courseId, request.bookId)

    // Check cache prima di rigenerare
    if (!request.forceRegenerate) {
      const cached = this.getCachedMindmap(cacheKey)
      if (cached) {
        console.log('🎯 Mindmap from cache:', { courseId: request.courseId, bookId: request.bookId })
        this.updateLastAccessed(cacheKey)
        return { mindmap: cached.data, fromCache: true }
      }
    }

    // Genera nuova mappa
    console.log('🔄 Generating new mindmap:', { courseId: request.courseId, bookId: request.bookId })

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/mindmap`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          course_id: request.courseId,
          book_id: request.bookId,
          topic: request.topic || 'Contenuti del libro',
          focus_areas: request.focusAreas || ['capitoli principali', 'concetti chiave', 'temi centrali']
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      const data = await response.json()

      if (!data.success || !data.mindmap) {
        throw new Error('Generazione mappa fallita')
      }

      // Salva in cache
      this.cacheMindmap(cacheKey, {
        data: data.mindmap,
        timestamp: Date.now(),
        courseId: request.courseId,
        bookId: request.bookId,
        version: CACHE_VERSION
      })

      // Salva anche storage persistente
      this.saveMindmapStorage({
        id: cacheKey,
        courseId: request.courseId,
        bookId: request.bookId,
        title: data.mindmap.title || 'Mappa Concettuale',
        mindmap: data.mindmap,
        markdown: data.markdown,
        references: data.references,
        sources: data.sources,
        createdAt: new Date().toISOString(),
        lastAccessed: new Date().toISOString()
      })

      console.log('✅ Mindmap generated and cached')
      return { mindmap: data.mindmap, fromCache: false }

    } catch (error) {
      console.error('❌ Mindmap generation failed:', error)
      return {
        mindmap: null,
        fromCache: false,
        error: error instanceof Error ? error.message : 'Errore generazione mappa'
      }
    }
  }

  /**
   * Espande un nodo della mappa mentale
   */
  async expandNode(
    courseId: string,
    bookId: string | undefined,
    nodeText: string,
    nodeContext: string[],
    customPrompt?: string
  ): Promise<{ expandedNodes: StudyMindmapNode[]; sources: string[] } | null> {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/mindmap/expand`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          course_id: courseId,
          book_id: bookId,
          node_text: nodeText,
          node_context: nodeContext.join(' > '),
          max_children: 4,
          expansion_prompt: customPrompt || undefined
        }),
      })

      if (!response.ok) return null

      const data = await response.json()

      if (!data.success || !data.expanded_nodes) return null

      const expandedNodes: StudyMindmapNode[] = data.expanded_nodes.map((child: any) => ({
        id: child.id,
        title: child.title,
        summary: child.summary ?? '',
        ai_hint: child.ai_hint ?? '',
        study_actions: child.study_actions ?? [],
        priority: child.priority ?? null,
        references: child.references ?? [],
        children: []
      }))

      // Aggiorna la mappa in cache con i nuovi nodi
      const cacheKey = this.buildCacheKey(courseId, bookId)
      this.updateMindmapWithExpandedNodes(cacheKey, nodeText, expandedNodes)

      return {
        expandedNodes,
        sources: data.sources_used || []
      }

    } catch (error) {
      console.error('❌ Node expansion failed:', error)
      return null
    }
  }

  /**
   * Recupera tutte le mappe salvate per un corso
   */
  getSavedMindmaps(courseId: string, bookId?: string): MindmapStorage[] {
    const storageKey = `mindmaps_${courseId}${bookId ? `_${bookId}` : ''}`
    const stored = localStorage.getItem(storageKey)

    if (!stored) return []

    try {
      const parsed = JSON.parse(stored)
      return Array.isArray(parsed) ? parsed : []
    } catch {
      return []
    }
  }

  /**
   * Elimina una mappa salvata
   */
  deleteSavedMindmap(courseId: string, bookId: string, mindmapId: string): boolean {
    try {
      const mindmaps = this.getSavedMindmaps(courseId, bookId)
      const filtered = mindmaps.filter(m => m.id !== mindmapId)

      const storageKey = `mindmaps_${courseId}${bookId ? `_${bookId}` : ''}`
      localStorage.setItem(storageKey, JSON.stringify(filtered))

      // Rimuovi anche dalla cache
      const cacheKey = this.buildCacheKey(courseId, bookId)
      this.cache.delete(cacheKey)
      this.saveCacheToStorage()

      return true
    } catch {
      return false
    }
  }

  /**
   * Converte StudyMindmap in CourseConceptMap per compatibilità
   */
  convertToConceptMap(mindmap: StudyMindmap): any {
    if (!mindmap || !mindmap.nodes) return null

    const convertNode = (node: StudyMindmapNode, depth = 0): any => {
      return {
        id: node.id,
        title: node.title,
        description: node.summary || '',
        depth,
        importance: node.priority || 1,
        study_actions: node.study_actions || [],
        ai_hint: node.ai_hint || '',
        references: node.references || [],
        children: node.children ? node.children.map(child => convertNode(child, depth + 1)) : []
      }
    }

    return {
      concepts: mindmap.nodes.map(node => convertNode(node)),
      metadata: {
        title: mindmap.title,
        generated_at: new Date().toISOString(),
        total_concepts: mindmap.nodes.length
      }
    }
  }

  // === Metodi Privati ===

  private buildCacheKey(courseId: string, bookId?: string): string {
    return bookId ? `${CACHE_KEY_PREFIX}${courseId}_${bookId}` : `${CACHE_KEY_PREFIX}${courseId}`
  }

  private getCachedMindmap(cacheKey: string): MindmapCache | null {
    const cached = this.cache.get(cacheKey)
    if (!cached) return null

    // Check expirazione
    const age = Date.now() - cached.timestamp
    const maxAge = CACHE_EXPIRY_HOURS * 60 * 60 * 1000

    if (age > maxAge) {
      this.cache.delete(cacheKey)
      return null
    }

    return cached
  }

  private cacheMindmap(cacheKey: string, cacheData: MindmapCache): void {
    this.cache.set(cacheKey, cacheData)
    this.saveCacheToStorage()
  }

  private updateLastAccessed(cacheKey: string): void {
    const storageKey = `mindmaps_storage_${cacheKey}`
    const stored = localStorage.getItem(storageKey)

    if (stored) {
      try {
        const storage = JSON.parse(stored)
        storage.lastAccessed = new Date().toISOString()
        localStorage.setItem(storageKey, JSON.stringify(storage))
      } catch (error) {
        console.error('Error updating last accessed:', error)
      }
    }
  }

  private updateMindmapWithExpandedNodes(cacheKey: string, nodeTitle: string, expandedNodes: StudyMindmapNode[]): void {
    const cached = this.getCachedMindmap(cacheKey)
    if (!cached) return

    const updatedMindmap = this.addNodeToMindmap(cached.data, nodeTitle, expandedNodes)

    // Aggiorna cache
    this.cacheMindmap(cacheKey, {
      ...cached,
      data: updatedMindmap,
      timestamp: Date.now()
    })

    // Aggiorna storage
    this.updateMindmapStorage(cacheKey, updatedMindmap)
  }

  private addNodeToMindmap(mindmap: StudyMindmap, targetTitle: string, newNodes: StudyMindmapNode[]): StudyMindmap {
    const updateNodes = (nodes: StudyMindmapNode[]): StudyMindmapNode[] => {
      return nodes.map(node => {
        if (node.title === targetTitle) {
          const existingIds = new Set(node.children.map(child => child.id))
          const existingTitles = new Set(node.children.map(child => child.title.toLowerCase()))

          const filteredNewNodes = newNodes.filter(newNode =>
            !existingIds.has(newNode.id) && !existingTitles.has(newNode.title.toLowerCase())
          )

          return {
            ...node,
            children: [...node.children, ...filteredNewNodes]
          }
        }

        if (node.children.length > 0) {
          return {
            ...node,
            children: updateNodes(node.children)
          }
        }

        return node
      })
    }

    return {
      ...mindmap,
      nodes: updateNodes(mindmap.nodes)
    }
  }

  private saveMindmapStorage(storage: MindmapStorage): void {
    try {
      const storageKey = `mindmaps_${storage.courseId}${storage.bookId ? `_${storage.bookId}` : ''}`
      const existing = this.getSavedMindmaps(storage.courseId, storage.bookId)

      // Rimuovi duplicati
      const filtered = existing.filter(m => m.id !== storage.id)
      const updated = [storage, ...filtered]

      localStorage.setItem(storageKey, JSON.stringify(updated))

      // Salva anche storage individuale
      const individualKey = `mindmaps_storage_${storage.id}`
      localStorage.setItem(individualKey, JSON.stringify(storage))

    } catch (error) {
      console.error('Error saving mindmap storage:', error)
    }
  }

  private updateMindmapStorage(cacheKey: string, mindmap: StudyMindmap): void {
    const individualKey = `mindmaps_storage_${cacheKey}`
    const stored = localStorage.getItem(individualKey)

    if (stored) {
      try {
        const storage = JSON.parse(stored)
        storage.mindmap = mindmap
        storage.lastAccessed = new Date().toISOString()
        localStorage.setItem(individualKey, JSON.stringify(storage))
      } catch (error) {
        console.error('Error updating mindmap storage:', error)
      }
    }
  }

  private loadCacheFromStorage(): void {
    try {
      const cached = localStorage.getItem('mindmap_cache')
      if (cached) {
        const data = JSON.parse(cached)
        this.cache = new Map(Object.entries(data))
      }
    } catch (error) {
      console.error('Error loading cache from storage:', error)
    }
  }

  private saveCacheToStorage(): void {
    try {
      const data = Object.fromEntries(this.cache)
      localStorage.setItem('mindmap_cache', JSON.stringify(data))
    } catch (error) {
      console.error('Error saving cache to storage:', error)
    }
  }

  private cleanExpiredCache(): void {
    const now = Date.now()
    const maxAge = CACHE_EXPIRY_HOURS * 60 * 60 * 1000

    for (const [key, cache] of this.cache.entries()) {
      if (now - cache.timestamp > maxAge) {
        this.cache.delete(key)
      }
    }

    this.saveCacheToStorage()
  }
}

// Esporta singleton
export const mindmapService = new MindmapService()
export default mindmapService