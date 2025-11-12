/**
 * AI Expansion Service for Concept Maps
 * Provides contextual AI-powered expansion with smart suggestions
 */

import { ConceptNode } from '@/stores/conceptMapStore'

export interface ExpansionPrompt {
  id: string
  title: string
  description: string
  template: string
  category: 'basic' | 'detailed' | 'examples' | 'applications' | 'connections'
  icon: string
}

export interface ExpansionSuggestion {
  type: 'subtopic' | 'example' | 'application' | 'connection' | 'detail'
  title: string
  description: string
  prompt: string
  confidence: number
  estimatedNodes: number
}

export interface ExpansionResult {
  success: boolean
  nodes: ConceptNode[]
  relationships?: Array<{
    from: string
    to: string
    type: string
    description: string
  }>
  suggestions?: ExpansionSuggestion[]
  metadata?: {
    expansionType: string
    aiModel: string
    processingTime: number
    quality: number
  }
}

class AIExpansionService {
  private baseUrl: string
  private defaultPrompts: ExpansionPrompt[]

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    this.defaultPrompts = this.initializeDefaultPrompts()
  }

  private initializeDefaultPrompts(): ExpansionPrompt[] {
    return [
      {
        id: 'basic-expansion',
        title: 'Espansione Base',
        description: 'Scomponi il concetto nei suoi elementi fondamentali',
        template: 'Analizza il concetto "{concept}" e identificane i componenti principali, le definizioni chiave e gli aspetti fondamentali. Organizza i risultati in una struttura gerarchica chiara.',
        category: 'basic',
        icon: '📋'
      },
      {
        id: 'detailed-analysis',
        title: 'Analisi Dettagliata',
        description: 'Approfondisci ogni aspetto del concetto',
        template: 'Fornisci un\'analisi approfondita del concetto "{concept}", includendo: definizioni precise, caratteristiche distintive, contesto storico e teorico, e suddivisioni logiche.',
        category: 'detailed',
        icon: '🔍'
      },
      {
        id: 'practical-examples',
        title: 'Esempi Pratici',
        description: 'Mostra esempi concreti e applicazioni',
        template: 'Genera esempi pratici e casi d\'uso reali per il concetto "{concept}". Include esempi diversi, contesti applicativi e scenari di utilizzo.',
        category: 'examples',
        icon: '💡'
      },
      {
        id: 'theoretical-connections',
        title: 'Connessioni Teoriche',
        description: 'Collega il concetto ad altre teorie e discipline',
        template: 'Identifica le connessioni tra il concetto "{concept}" e altri concetti correlati, teorie o discipline. Spiega le relazioni e le interdipendenze.',
        category: 'connections',
        icon: '🔗'
      },
      {
        id: 'historical-evolution',
        title: 'Evoluzione Storica',
        description: 'Traccia lo sviluppo storico del concetto',
        template: 'Descrivi l\'evoluzione storica del concetto "{concept}", incluse le origini, i principali sviluppi, i contributori chiave e le applicazioni moderne.',
        category: 'detailed',
        icon: '📜'
      },
      {
        id: 'modern-applications',
        title: 'Applicazioni Moderne',
        description: 'Esplora le applicazioni contemporanee',
        template: 'Analizza le applicazioni moderne e attuali del concetto "{concept}" nel contesto tecnologico, scientifico e professionale odierno.',
        category: 'applications',
        icon: '🚀'
      },
      {
        id: 'critical-analysis',
        title: 'Analisi Critica',
        description: 'Esamina limiti, critiche e prospettive future',
        template: 'Fornisci un\'analisi critica del concetto "{concept}", includendo limiti, critiche, controversie, e prospettive di sviluppo futuro.',
        category: 'detailed',
        icon: '⚖️'
      },
      {
        id: 'interdisciplinary-links',
        title: 'Collegamenti Interdisciplinari',
        description: 'Connetti con altre aree del sapere',
        template: 'Esplora i collegamenti interdisciplinari del concetto "{concept}" con diverse aree del sapere, evidenziando come viene applicato in vari contesti.',
        category: 'connections',
        icon: '🌐'
      }
    ]
  }

  // Get contextual prompts based on node characteristics
  getContextualPrompts(node: ConceptNode): ExpansionPrompt[] {
    const basePrompts = [...this.defaultPrompts]
    const contextualPrompts: ExpansionPrompt[] = []

    // Add depth-based prompts
    if (node.depth === 0) {
      contextualPrompts.push({
        id: 'foundational-concepts',
        title: 'Concetti Fondamentali',
        description: 'Identifica i concetti di base',
        template: 'Dato il concetto principale "{concept}", identifica i concetti fondamentali e le idee di base che ogni studente dovrebbe conoscere.',
        category: 'basic',
        icon: '🏛️'
      })
    }

    // Add subject-specific prompts based on tags
    if (node.tags) {
      if (node.tags.some(tag => tag.toLowerCase().includes('matematica') || tag.toLowerCase().includes('math'))) {
        contextualPrompts.push({
          id: 'mathematical-foundations',
          title: 'Fondamenti Matematici',
          description: 'Approfondisci gli aspetti matematici',
          template: 'Analizza gli aspetti matematici del concetto "{concept}", incluse formule, dimostrazioni, e applicazioni quantitative.',
          category: 'detailed',
          icon: '📐'
        })
      }

      if (node.tags.some(tag => tag.toLowerCase().includes('storia') || tag.toLowerCase().includes('history'))) {
        contextualPrompts.push({
          id: 'historical-context',
          title: 'Contesto Storico',
          description: 'Colloca il concetto nel suo contesto storico',
          template: 'Analizza il contesto storico del concetto "{concept}", includendo periodi chiave, eventi significativi e figure importanti.',
          category: 'detailed',
          icon: '📚'
        })
      }

      if (node.tags.some(tag => tag.toLowerCase().includes('scienza') || tag.toLowerCase().includes('science'))) {
        contextualPrompts.push({
          id: 'scientific-method',
          title: 'Metodo Scientifico',
          description: 'Applica il metodo scientifico',
          template: 'Applica il metodo scientifico al concetto "{concept}", includendo ipotesi, sperimentazione, osservazione e结论.',
          category: 'detailed',
          icon: '🔬'
        })
      }
    }

    // Add complexity-based prompts
    if (node.children && node.children.length > 3) {
      contextualPrompts.push({
        id: 'organization-structure',
        title: 'Struttura Organizzativa',
        description: 'Migliora l\'organizzazione dei sottotemi',
        template: 'Riorganizza e struttura i sottotemi del concetto "{concept}" in modo logico e gerarchico, identificando relazioni e dipendenze.',
        category: 'basic',
        icon: '🗂️'
      })
    }

    // Add mastery-based prompts
    if (node.masteryLevel && node.masteryLevel < 50) {
      contextualPrompts.push({
        id: 'learning-foundations',
        title: 'Basi per l\'Apprendimento',
        description: 'Parti dalle basi per apprendere',
        template: 'Scomponi il concetto "{concept}" in elementi semplici e facili da capire, partendo dalle basi e procedendo gradualmente.',
        category: 'basic',
        icon: '🎯'
      })
    } else if (node.masteryLevel && node.masteryLevel > 80) {
      contextualPrompts.push({
        id: 'advanced-topics',
        title: 'Argomenti Avanzati',
        description: 'Esplora aspetti complessi e avanzati',
        template: 'Approfondisci aspetti avanzati e complessi del concetto "{concept}", includendo temi specialistici e ricerca all\'avanguardia.',
        category: 'detailed',
        icon: '🚀'
      })
    }

    return [...basePrompts, ...contextualPrompts]
  }

  // Get smart suggestions based on context
  async getSmartSuggestions(node: ConceptNode): Promise<ExpansionSuggestion[]> {
    const suggestions: ExpansionSuggestion[] = []

    // Analyze current node state
    const hasFewChildren = !node.children || node.children.length < 3
    const hasNoExamples = !node.children?.some(child =>
      child.title.toLowerCase().includes('esempio') ||
      child.title.toLowerCase().includes('example')
    )
    const isDeepNode = node.depth !== undefined && node.depth > 2
    const hasLowMastery = node.masteryLevel !== undefined && node.masteryLevel < 50

    // Generate contextual suggestions
    if (hasFewChildren) {
      suggestions.push({
        type: 'subtopic',
        title: 'Aggiungi Sottotemi',
        description: 'Espandi questo concetto con argomenti principali',
        prompt: `Identifica i principali sottotemi del concetto "${node.title}"`,
        confidence: 0.9,
        estimatedNodes: 3
      })
    }

    if (hasNoExamples && !isDeepNode) {
      suggestions.push({
        type: 'example',
        title: 'Aggiungi Esempi',
        description: 'Includi esempi pratici e concreti',
        prompt: `Genera esempi pratici per il concetto "${node.title}"`,
        confidence: 0.85,
        estimatedNodes: 4
      })
    }

    if (isDeepNode && hasLowMastery) {
      suggestions.push({
        type: 'detail',
        title: 'Approfondisci Dettagli',
        description: 'Migliora la comprensione con dettagli aggiuntivi',
        prompt: `Fornisci spiegazioni dettagliate per "${node.title}"`,
        confidence: 0.8,
        estimatedNodes: 2
      })
    }

    // Add connection suggestions if not too deep
    if (!isDeepNode) {
      suggestions.push({
        type: 'connection',
        title: 'Trova Connessioni',
        description: 'Collega questo concetto ad altri argomenti',
        prompt: `Identifica concetti correlati a "${node.title}"`,
        confidence: 0.75,
        estimatedNodes: 3
      })
    }

    // Add application suggestions for practical subjects
    if (node.tags?.some(tag =>
      tag.toLowerCase().includes('pratica') ||
      tag.toLowerCase().includes('applicazione') ||
      tag.toLowerCase().includes('engineering')
    )) {
      suggestions.push({
        type: 'application',
        title: 'Applicazioni Pratiche',
        description: 'Mostra come si applica questo concetto',
        prompt: `Descrivi applicazioni pratiche del concetto "${node.title}"`,
        confidence: 0.8,
        estimatedNodes: 3
      })
    }

    return suggestions.sort((a, b) => b.confidence - a.confidence)
  }

  // Expand node with AI
  async expandNode(
    nodeId: string,
    prompt: string,
    courseId?: string,
    bookId?: string
  ): Promise<ExpansionResult> {
    try {
      const startTime = Date.now()

      const response = await fetch(`${this.baseUrl}/mindmap/expand`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          course_id: courseId,
          book_id: bookId,
          node_id: nodeId,
          prompt: prompt
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      const processingTime = Date.now() - startTime

      // Transform response data if needed
      const nodes = data.expanded_nodes || data.nodes || []
      const relationships = data.relationships || []

      // Generate additional suggestions
      const smartSuggestions = await this.getSmartSuggestions({
        id: nodeId,
        title: data.original_concept || 'Concept',
        children: nodes,
        depth: 0, // This would come from the actual node
        tags: [],
        study_actions: []
      })

      return {
        success: true,
        nodes,
        relationships,
        suggestions: smartSuggestions.slice(0, 3), // Limit to top 3
        metadata: {
          expansionType: 'ai_powered',
          aiModel: data.model || 'default',
          processingTime,
          quality: data.quality || 0.8
        }
      }

    } catch (error) {
      console.error('Error expanding node:', error)
      return {
        success: false,
        nodes: [],
        metadata: {
          expansionType: 'error',
          aiModel: 'none',
          processingTime: 0,
          quality: 0
        }
      }
    }
  }

  // Expand node with predefined prompt
  async expandNodeWithPrompt(
    node: ConceptNode,
    promptId: string,
    courseId?: string,
    bookId?: string
  ): Promise<ExpansionResult> {
    const prompts = this.getContextualPrompts(node)
    const prompt = prompts.find(p => p.id === promptId)

    if (!prompt) {
      throw new Error(`Prompt with id ${promptId} not found`)
    }

    const fullPrompt = prompt.template.replace('{concept}', node.title)
    return this.expandNode(node.id, fullPrompt, courseId, bookId)
  }

  // Get auto-generated prompt based on context
  getAutoPrompt(node: ConceptNode): string {
    const prompts = this.getContextualPrompts(node)

    // Select best prompt based on context
    if (node.depth === 0) {
      return prompts.find(p => p.id === 'foundational-concepts')?.template || prompts[0].template
    }

    if (node.masteryLevel && node.masteryLevel < 50) {
      return prompts.find(p => p.id === 'learning-foundations')?.template || prompts[0].template
    }

    if (node.children && node.children.length > 5) {
      return prompts.find(p => p.id === 'organization-structure')?.template || prompts[0].template
    }

    return prompts[0].template
  }

  // Quick expansion with smart prompt selection
  async quickExpand(
    node: ConceptNode,
    courseId?: string,
    bookId?: string
  ): Promise<ExpansionResult> {
    const autoPrompt = this.getAutoPrompt(node)
    const fullPrompt = autoPrompt.replace('{concept}', node.title)
    return this.expandNode(node.id, fullPrompt, courseId, bookId)
  }
}

// Export singleton instance
export const aiExpansionService = new AIExpansionService()

// React hook for AI expansion
export function useAIExpansion() {
  const expandNode = async (
    node: ConceptNode,
    prompt: string,
    courseId?: string,
    bookId?: string
  ) => {
    return aiExpansionService.expandNode(node.id, prompt, courseId, bookId)
  }

  const expandNodeWithPrompt = async (
    node: ConceptNode,
    promptId: string,
    courseId?: string,
    bookId?: string
  ) => {
    return aiExpansionService.expandNodeWithPrompt(node, promptId, courseId, bookId)
  }

  const quickExpand = async (
    node: ConceptNode,
    courseId?: string,
    bookId?: string
  ) => {
    return aiExpansionService.quickExpand(node, courseId, bookId)
  }

  const getPrompts = (node: ConceptNode) => {
    return aiExpansionService.getContextualPrompts(node)
  }

  const getSuggestions = (node: ConceptNode) => {
    return aiExpansionService.getSmartSuggestions(node)
  }

  return {
    expandNode,
    expandNodeWithPrompt,
    quickExpand,
    getPrompts,
    getSuggestions
  }
}