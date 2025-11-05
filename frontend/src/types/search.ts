export type SearchType = 'text' | 'semantic' | 'hybrid'

export type SortOrder = 'relevance' | 'date' | 'alphabetical' | 'confidence'

export interface SearchMetadata {
  highlights?: string[]
  matched_terms?: string[]
  annotation_type?: string
  is_public?: boolean
  is_favorite?: boolean
  total_pages?: number
  [key: string]: unknown
}

export interface SearchResult {
  id: string
  type: 'annotation' | 'pdf_content' | 'ocr_result' | string
  content: string
  title: string
  source: string
  course_id: string
  book_id: string
  page_number?: number
  user_id?: string
  score: number
  confidence?: number
  tags?: string[]
  created_at?: string
  metadata?: SearchMetadata
}

export type SearchFacets = Record<string, Record<string, number>>

export interface AdvancedSearchResponse {
  query: string
  results: SearchResult[]
  total_count: number
  has_more: boolean
  search_time: number
  facets?: SearchFacets
  suggestions?: string[]
}
