# Advanced Features 6: Advanced Search and Filtering - Powerful Discovery Features

## 🎯 **Learning Objectives**

By the end of this tutorial, you will:
- Build sophisticated full-text search with relevance scoring
- Implement faceted search with multiple filter dimensions
- Create semantic search using vector embeddings
- Build search suggestions and autocomplete functionality
- Implement saved searches and search history
- Create advanced filtering with boolean logic and date ranges

## 🔍 **The Advanced Search Challenge**

Modern chat applications need powerful search capabilities:
- **Full-Text Search**: Find messages by content across all conversations
- **Semantic Understanding**: Match meaning, not just keywords
- **Faceted Filtering**: Filter by agent, date, topic, sentiment, etc.
- **Real-Time Suggestions**: Help users discover relevant content
- **Search Analytics**: Track what users search for and improve results
- **Performance at Scale**: Fast search across thousands of messages

**Our goal**: Build **Google-level search experience** for conversation data.

## 🎯 **Advanced Search Architecture**

### **Step 1: Search Index Models**

```typescript
// src/types/advancedSearch.ts
export interface SearchIndex {
  // Document identification
  documentId: string
  documentType: 'message' | 'conversation' | 'thread'
  
  // Content fields
  title?: string
  content: string
  summary?: string
  
  // Searchable metadata
  agentName?: string
  agentProtocol?: string
  conversationId: string
  threadId?: string
  
  // Temporal information
  timestamp: Date
  dateCreated: Date
  lastModified: Date
  
  // Classification
  topics: string[]
  entities: string[]
  keywords: string[]
  sentiment: 'positive' | 'neutral' | 'negative'
  language: string
  
  // Content analysis
  wordCount: number
  readingTime: number // minutes
  complexity: 'simple' | 'moderate' | 'complex'
  
  // User interaction
  userRating?: number
  bookmarked: boolean
  shared: boolean
  
  // Vector embeddings for semantic search
  embedding?: number[]
  embeddingModel?: string
}

export interface SearchQuery {
  // Basic query
  text: string
  queryType: 'keyword' | 'phrase' | 'semantic' | 'fuzzy'
  
  // Filters
  filters: {
    dateRange?: {
      start: Date
      end: Date
    }
    agents?: string[]
    protocols?: string[]
    topics?: string[]
    sentiment?: string[]
    conversations?: string[]
    threads?: string[]
    bookmarked?: boolean
    shared?: boolean
    languages?: string[]
    complexity?: string[]
  }
  
  // Search modifiers
  options: {
    fuzzyTolerance?: number
    semanticThreshold?: number
    includeArchived?: boolean
    includePrivate?: boolean
    maxResults?: number
    offset?: number
  }
  
  // Result preferences
  sorting: {
    field: 'relevance' | 'date' | 'rating' | 'length'
    direction: 'asc' | 'desc'
  }
  
  // Advanced query syntax
  booleanLogic?: BooleanQuery
  proximitySearch?: ProximityQuery[]
}

export interface BooleanQuery {
  operator: 'AND' | 'OR' | 'NOT'
  clauses: Array<{
    field?: string
    value: string
    operator: 'MUST' | 'SHOULD' | 'MUST_NOT'
    boost?: number
  }>
}

export interface ProximityQuery {
  terms: string[]
  distance: number // words apart
  inOrder: boolean
}

export interface SearchResult {
  // Document info
  document: SearchIndex
  originalMessage?: StoredMessage
  
  // Relevance
  score: number
  explanation?: string
  
  // Highlighting
  highlights: {
    field: string
    fragments: string[]
    matchPositions: Array<{ start: number; end: number }>
  }[]
  
  // Context
  conversationContext?: {
    beforeMessages: StoredMessage[]
    afterMessages: StoredMessage[]
  }
}

export interface SearchSuggestion {
  type: 'query' | 'filter' | 'agent' | 'topic' | 'conversation'
  text: string
  displayText: string
  description?: string
  frequency: number
  category?: string
}

export interface SearchFacets {
  agents: Array<{ name: string; count: number; selected: boolean }>
  topics: Array<{ name: string; count: number; selected: boolean }>
  dateRanges: Array<{ label: string; start: Date; end: Date; count: number }>
  sentiment: Array<{ value: string; count: number; selected: boolean }>
  protocols: Array<{ name: string; count: number; selected: boolean }>
  conversations: Array<{ id: string; title: string; count: number }>
  languages: Array<{ code: string; name: string; count: number }>
}
```

### **Step 2: Advanced Search Engine**

```typescript
// src/services/advancedSearchService.ts
interface SearchConfig {
  indexName: string
  maxIndexSize: number
  enableVectorSearch: boolean
  enableFacetedSearch: boolean
  embeddingModel: string
  searchAnalytics: boolean
}

export class AdvancedSearchService {
  private config: SearchConfig
  private searchIndex = new Map<string, SearchIndex>()
  private vectorIndex?: VectorIndex
  private suggestionEngine?: SuggestionEngine
  private searchAnalytics?: SearchAnalytics

  constructor(config: Partial<SearchConfig> = {}) {
    this.config = {
      indexName: 'conversation_search',
      maxIndexSize: 100000,
      enableVectorSearch: true,
      enableFacetedSearch: true,
      embeddingModel: 'sentence-transformers/all-MiniLM-L6-v2',
      searchAnalytics: true,
      ...config
    }

    this.initialize()
  }

  /**
   * Advanced search with multiple query types and filters
   */
  async search(query: SearchQuery): Promise<{
    results: SearchResult[]
    facets: SearchFacets
    suggestions: SearchSuggestion[]
    totalResults: number
    searchTime: number
  }> {
    const startTime = performance.now()
    
    try {
      // Track search analytics
      if (this.searchAnalytics) {
        this.searchAnalytics.trackSearch(query)
      }

      let results: SearchResult[] = []

      // Execute search based on query type
      switch (query.queryType) {
        case 'semantic':
          results = await this.performSemanticSearch(query)
          break
        case 'fuzzy':
          results = await this.performFuzzySearch(query)
          break
        case 'phrase':
          results = await this.performPhraseSearch(query)
          break
        default:
          results = await this.performKeywordSearch(query)
      }

      // Apply filters
      results = this.applyFilters(results, query.filters)

      // Apply boolean logic if specified
      if (query.booleanLogic) {
        results = this.applyBooleanLogic(results, query.booleanLogic, query.text)
      }

      // Sort results
      results = this.sortResults(results, query.sorting)

      // Apply pagination
      const { maxResults = 50, offset = 0 } = query.options
      const paginatedResults = results.slice(offset, offset + maxResults)

      // Generate facets
      const facets = this.config.enableFacetedSearch 
        ? this.generateFacets(results, query.filters)
        : this.getEmptyFacets()

      // Generate suggestions
      const suggestions = this.suggestionEngine 
        ? await this.suggestionEngine.getSuggestions(query.text, results)
        : []

      // Add context to results
      const enrichedResults = await this.enrichResultsWithContext(paginatedResults)

      const searchTime = performance.now() - startTime

      return {
        results: enrichedResults,
        facets,
        suggestions,
        totalResults: results.length,
        searchTime,
      }
    } catch (error) {
      console.error('Search failed:', error)
      throw error
    }
  }

  /**
   * Add document to search index
   */
  async indexDocument(document: SearchIndex): Promise<void> {
    // Generate embeddings for semantic search
    if (this.config.enableVectorSearch && this.vectorIndex) {
      const embedding = await this.generateEmbedding(document.content)
      document.embedding = embedding
      document.embeddingModel = this.config.embeddingModel
      
      await this.vectorIndex.addDocument(document.documentId, embedding, document)
    }

    // Add to main index
    this.searchIndex.set(document.documentId, document)

    // Update suggestion engine
    if (this.suggestionEngine) {
      this.suggestionEngine.addDocument(document)
    }

    // Cleanup if index is too large
    if (this.searchIndex.size > this.config.maxIndexSize) {
      await this.cleanupOldDocuments()
    }
  }

  /**
   * Get search suggestions as user types
   */
  async getSuggestions(partialQuery: string, limit = 10): Promise<SearchSuggestion[]> {
    if (!this.suggestionEngine || partialQuery.length < 2) {
      return []
    }

    return this.suggestionEngine.getSuggestions(partialQuery, [], limit)
  }

  /**
   * Get popular searches and trends
   */
  async getSearchTrends(timeframe: 'day' | 'week' | 'month' = 'week'): Promise<{
    popularQueries: Array<{ query: string; count: number }>
    trendingTopics: Array<{ topic: string; growth: number }>
    searchVolume: number
  }> {
    if (!this.searchAnalytics) {
      return { popularQueries: [], trendingTopics: [], searchVolume: 0 }
    }

    return this.searchAnalytics.getTrends(timeframe)
  }

  // Private implementation methods

  private async initialize(): Promise<void> {
    // Initialize vector search if enabled
    if (this.config.enableVectorSearch) {
      this.vectorIndex = new VectorIndex({
        dimensions: 384, // MiniLM-L6-v2 dimension size
        metric: 'cosine',
      })
    }

    // Initialize suggestion engine
    this.suggestionEngine = new SuggestionEngine()

    // Initialize search analytics
    if (this.config.searchAnalytics) {
      this.searchAnalytics = new SearchAnalytics()
    }

    // Load existing index from storage
    await this.loadIndexFromStorage()
  }

  private async performSemanticSearch(query: SearchQuery): Promise<SearchResult[]> {
    if (!this.vectorIndex) {
      // Fallback to keyword search
      return this.performKeywordSearch(query)
    }

    try {
      // Generate query embedding
      const queryEmbedding = await this.generateEmbedding(query.text)
      
      // Find similar documents
      const similarDocuments = await this.vectorIndex.search(
        queryEmbedding,
        query.options.maxResults || 50,
        query.options.semanticThreshold || 0.7
      )

      // Convert to search results
      const results: SearchResult[] = similarDocuments.map(result => ({
        document: result.document,
        score: result.similarity,
        explanation: `Semantic similarity: ${(result.similarity * 100).toFixed(1)}%`,
        highlights: this.generateSemanticHighlights(query.text, result.document.content),
      }))

      return results
    } catch (error) {
      console.warn('Semantic search failed, falling back to keyword search:', error)
      return this.performKeywordSearch(query)
    }
  }

  private async performKeywordSearch(query: SearchQuery): Promise<SearchResult[]> {
    const queryTerms = this.tokenizeQuery(query.text)
    const results: SearchResult[] = []

    for (const [docId, document] of this.searchIndex) {
      const score = this.calculateKeywordScore(queryTerms, document)
      
      if (score > 0) {
        results.push({
          document,
          score,
          explanation: `Keyword match score: ${score.toFixed(2)}`,
          highlights: this.generateKeywordHighlights(queryTerms, document.content),
        })
      }
    }

    return results
  }

  private async performFuzzySearch(query: SearchQuery): Promise<SearchResult[]> {
    const tolerance = query.options.fuzzyTolerance || 2
    const queryTerms = this.tokenizeQuery(query.text)
    const results: SearchResult[] = []

    for (const [docId, document] of this.searchIndex) {
      const score = this.calculateFuzzyScore(queryTerms, document, tolerance)
      
      if (score > 0) {
        results.push({
          document,
          score,
          explanation: `Fuzzy match score: ${score.toFixed(2)} (tolerance: ${tolerance})`,
          highlights: this.generateFuzzyHighlights(queryTerms, document.content, tolerance),
        })
      }
    }

    return results
  }

  private async performPhraseSearch(query: SearchQuery): Promise<SearchResult[]> {
    const phrase = query.text.toLowerCase()
    const results: SearchResult[] = []

    for (const [docId, document] of this.searchIndex) {
      const content = document.content.toLowerCase()
      const matches = this.findPhraseMatches(phrase, content)
      
      if (matches.length > 0) {
        const score = matches.length * 2 // Boost phrase matches
        results.push({
          document,
          score,
          explanation: `Exact phrase matches: ${matches.length}`,
          highlights: this.generatePhraseHighlights(phrase, document.content, matches),
        })
      }
    }

    return results
  }

  private applyFilters(results: SearchResult[], filters: SearchQuery['filters']): SearchResult[] {
    return results.filter(result => {
      const doc = result.document

      // Date range filter
      if (filters.dateRange) {
        const docDate = new Date(doc.timestamp)
        if (docDate < filters.dateRange.start || docDate > filters.dateRange.end) {
          return false
        }
      }

      // Agent filter
      if (filters.agents && filters.agents.length > 0) {
        if (!doc.agentName || !filters.agents.includes(doc.agentName)) {
          return false
        }
      }

      // Protocol filter
      if (filters.protocols && filters.protocols.length > 0) {
        if (!doc.agentProtocol || !filters.protocols.includes(doc.agentProtocol)) {
          return false
        }
      }

      // Topic filter
      if (filters.topics && filters.topics.length > 0) {
        if (!doc.topics.some(topic => filters.topics!.includes(topic))) {
          return false
        }
      }

      // Sentiment filter
      if (filters.sentiment && filters.sentiment.length > 0) {
        if (!filters.sentiment.includes(doc.sentiment)) {
          return false
        }
      }

      // Conversation filter
      if (filters.conversations && filters.conversations.length > 0) {
        if (!filters.conversations.includes(doc.conversationId)) {
          return false
        }
      }

      // Bookmarked filter
      if (filters.bookmarked !== undefined) {
        if (doc.bookmarked !== filters.bookmarked) {
          return false
        }
      }

      return true
    })
  }

  private generateFacets(results: SearchResult[], currentFilters: SearchQuery['filters']): SearchFacets {
    const facets: SearchFacets = {
      agents: [],
      topics: [],
      dateRanges: [],
      sentiment: [],
      protocols: [],
      conversations: [],
      languages: [],
    }

    // Count occurrences for each facet
    const agentCounts = new Map<string, number>()
    const topicCounts = new Map<string, number>()
    const sentimentCounts = new Map<string, number>()
    const protocolCounts = new Map<string, number>()
    const conversationCounts = new Map<string, number>()
    const languageCounts = new Map<string, number>()

    for (const result of results) {
      const doc = result.document

      // Count agents
      if (doc.agentName) {
        agentCounts.set(doc.agentName, (agentCounts.get(doc.agentName) || 0) + 1)
      }

      // Count topics
      for (const topic of doc.topics) {
        topicCounts.set(topic, (topicCounts.get(topic) || 0) + 1)
      }

      // Count sentiment
      sentimentCounts.set(doc.sentiment, (sentimentCounts.get(doc.sentiment) || 0) + 1)

      // Count protocols
      if (doc.agentProtocol) {
        protocolCounts.set(doc.agentProtocol, (protocolCounts.get(doc.agentProtocol) || 0) + 1)
      }

      // Count languages
      languageCounts.set(doc.language, (languageCounts.get(doc.language) || 0) + 1)
    }

    // Convert to facet format
    facets.agents = Array.from(agentCounts.entries())
      .map(([name, count]) => ({
        name,
        count,
        selected: currentFilters.agents?.includes(name) || false,
      }))
      .sort((a, b) => b.count - a.count)

    facets.topics = Array.from(topicCounts.entries())
      .map(([name, count]) => ({
        name,
        count,
        selected: currentFilters.topics?.includes(name) || false,
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 20) // Limit to top topics

    facets.sentiment = Array.from(sentimentCounts.entries())
      .map(([value, count]) => ({
        value,
        count,
        selected: currentFilters.sentiment?.includes(value) || false,
      }))

    facets.protocols = Array.from(protocolCounts.entries())
      .map(([name, count]) => ({
        name,
        count,
        selected: currentFilters.protocols?.includes(name) || false,
      }))

    facets.languages = Array.from(languageCounts.entries())
      .map(([code, count]) => ({
        code,
        name: this.getLanguageName(code),
        count,
      }))

    // Generate date range facets
    facets.dateRanges = this.generateDateRangeFacets(results)

    return facets
  }

  private calculateKeywordScore(queryTerms: string[], document: SearchIndex): number {
    let score = 0
    const contentLower = document.content.toLowerCase()
    const titleLower = (document.title || '').toLowerCase()

    for (const term of queryTerms) {
      const termLower = term.toLowerCase()
      
      // Count occurrences in content
      const contentMatches = (contentLower.match(new RegExp(termLower, 'g')) || []).length
      score += contentMatches

      // Boost for title matches
      const titleMatches = (titleLower.match(new RegExp(termLower, 'g')) || []).length
      score += titleMatches * 3

      // Boost for exact topic matches
      if (document.topics.some(topic => topic.toLowerCase().includes(termLower))) {
        score += 5
      }

      // Boost for keyword matches
      if (document.keywords.some(keyword => keyword.toLowerCase().includes(termLower))) {
        score += 2
      }
    }

    // Length normalization
    const lengthFactor = Math.log(document.wordCount + 1)
    return score / lengthFactor
  }

  private generateKeywordHighlights(queryTerms: string[], content: string): Array<{
    field: string
    fragments: string[]
    matchPositions: Array<{ start: number; end: number }>
  }> {
    const highlights = []
    const matchPositions: Array<{ start: number; end: number }> = []
    const fragments: string[] = []

    for (const term of queryTerms) {
      const regex = new RegExp(term, 'gi')
      let match
      while ((match = regex.exec(content)) !== null) {
        matchPositions.push({
          start: match.index,
          end: match.index + term.length
        })
      }
    }

    // Generate context fragments around matches
    for (const position of matchPositions.slice(0, 5)) { // Limit to 5 fragments
      const start = Math.max(0, position.start - 50)
      const end = Math.min(content.length, position.end + 50)
      const fragment = content.substring(start, end)
      fragments.push(fragment)
    }

    return [{
      field: 'content',
      fragments,
      matchPositions
    }]
  }

  private async enrichResultsWithContext(results: SearchResult[]): Promise<SearchResult[]> {
    for (const result of results) {
      if (result.document.documentType === 'message') {
        // Add conversation context
        try {
          const contextMessages = await messageStorage.loadMessages(
            result.document.conversationId,
            { 
              before: result.document.timestamp,
              after: new Date(result.document.timestamp.getTime() - 60000), // 1 minute before
              limit: 5 
            }
          )
          
          const messageIndex = contextMessages.findIndex(m => m.id === result.document.documentId)
          if (messageIndex >= 0) {
            result.conversationContext = {
              beforeMessages: contextMessages.slice(Math.max(0, messageIndex - 2), messageIndex),
              afterMessages: contextMessages.slice(messageIndex + 1, messageIndex + 3)
            }
          }
        } catch (error) {
          console.warn('Failed to load context for result:', result.document.documentId)
        }
      }
    }

    return results
  }

  // Additional helper methods...

  private tokenizeQuery(query: string): string[] {
    return query
      .toLowerCase()
      .replace(/[^\w\s]/g, ' ')
      .split(/\s+/)
      .filter(term => term.length > 2)
  }

  private async generateEmbedding(text: string): Promise<number[]> {
    // In a real implementation, this would call an embedding API
    // For now, return a mock embedding
    return Array(384).fill(0).map(() => Math.random())
  }

  private getLanguageName(code: string): string {
    const languages: Record<string, string> = {
      'en': 'English',
      'es': 'Spanish', 
      'fr': 'French',
      'de': 'German',
      'zh': 'Chinese',
      'ja': 'Japanese',
    }
    return languages[code] || code.toUpperCase()
  }

  private sortResults(results: SearchResult[], sorting: SearchQuery['sorting']): SearchResult[] {
    return results.sort((a, b) => {
      let comparison = 0

      switch (sorting.field) {
        case 'date':
          comparison = a.document.timestamp.getTime() - b.document.timestamp.getTime()
          break
        case 'rating':
          comparison = (a.document.userRating || 0) - (b.document.userRating || 0)
          break
        case 'length':
          comparison = a.document.wordCount - b.document.wordCount
          break
        case 'relevance':
        default:
          comparison = b.score - a.score
      }

      return sorting.direction === 'desc' ? -comparison : comparison
    })
  }

  private generateDateRangeFacets(results: SearchResult[]): SearchFacets['dateRanges'] {
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000)
    const lastWeek = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)
    const lastMonth = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000)

    const ranges = [
      { label: 'Today', start: today, end: now },
      { label: 'Yesterday', start: yesterday, end: today },
      { label: 'Last 7 days', start: lastWeek, end: now },
      { label: 'Last 30 days', start: lastMonth, end: now },
    ]

    return ranges.map(range => ({
      ...range,
      count: results.filter(result => 
        result.document.timestamp >= range.start && 
        result.document.timestamp <= range.end
      ).length
    }))
  }

  private getEmptyFacets(): SearchFacets {
    return {
      agents: [],
      topics: [],
      dateRanges: [],
      sentiment: [],
      protocols: [],
      conversations: [],
      languages: [],
    }
  }
}

// Supporting classes (simplified implementations)
class VectorIndex {
  constructor(private config: { dimensions: number; metric: string }) {}
  
  async addDocument(id: string, embedding: number[], document: SearchIndex): Promise<void> {
    // Vector storage implementation
  }
  
  async search(queryEmbedding: number[], limit: number, threshold: number): Promise<Array<{
    document: SearchIndex
    similarity: number
  }>> {
    // Vector search implementation
    return []
  }
}

class SuggestionEngine {
  private queryHistory = new Map<string, number>()
  
  addDocument(document: SearchIndex): void {
    // Build suggestion corpus from document content
  }
  
  async getSuggestions(query: string, results: SearchResult[], limit = 10): Promise<SearchSuggestion[]> {
    // Generate suggestions based on query and results
    return []
  }
}

class SearchAnalytics {
  trackSearch(query: SearchQuery): void {
    // Track search patterns and usage
  }
  
  async getTrends(timeframe: string): Promise<{
    popularQueries: Array<{ query: string; count: number }>
    trendingTopics: Array<{ topic: string; growth: number }>
    searchVolume: number
  }> {
    return {
      popularQueries: [],
      trendingTopics: [],
      searchVolume: 0
    }
  }
}

export const advancedSearch = new AdvancedSearchService()
```

### **Step 3: Advanced Search UI Component**

```typescript
// src/components/AdvancedSearchInterface.tsx
import React, { useState, useEffect, useMemo, useCallback } from 'react'
import { Search, Filter, Calendar, Tag, User, Brain, ChevronDown, X, Bookmark } from 'lucide-react'
import { SearchQuery, SearchResult, SearchFacets, SearchSuggestion } from '../types/advancedSearch'
import { advancedSearch } from '../services/advancedSearchService'

interface AdvancedSearchInterfaceProps {
  onResultSelect: (result: SearchResult) => void
  className?: string
}

export const AdvancedSearchInterface: React.FC<AdvancedSearchInterfaceProps> = ({
  onResultSelect,
  className = '',
}) => {
  const [query, setQuery] = useState<SearchQuery>({
    text: '',
    queryType: 'keyword',
    filters: {},
    options: { maxResults: 20 },
    sorting: { field: 'relevance', direction: 'desc' },
  })

  const [results, setResults] = useState<SearchResult[]>([])
  const [facets, setFacets] = useState<SearchFacets | null>(null)
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const [searchStats, setSearchStats] = useState<{ total: number; time: number } | null>(null)

  // Debounced search
  const debouncedSearch = useMemo(
    () => debounce(async (searchQuery: SearchQuery) => {
      if (!searchQuery.text.trim()) {
        setResults([])
        setFacets(null)
        setSearchStats(null)
        return
      }

      setIsLoading(true)
      try {
        const response = await advancedSearch.search(searchQuery)
        setResults(response.results)
        setFacets(response.facets)
        setSuggestions(response.suggestions)
        setSearchStats({
          total: response.totalResults,
          time: response.searchTime
        })
      } catch (error) {
        console.error('Search failed:', error)
        setResults([])
        setFacets(null)
      } finally {
        setIsLoading(false)
      }
    }, 300),
    []
  )

  // Trigger search when query changes
  useEffect(() => {
    debouncedSearch(query)
  }, [query, debouncedSearch])

  // Get suggestions as user types
  useEffect(() => {
    if (query.text.length >= 2) {
      advancedSearch.getSuggestions(query.text).then(setSuggestions)
    } else {
      setSuggestions([])
    }
  }, [query.text])

  const updateQuery = useCallback((updates: Partial<SearchQuery>) => {
    setQuery(prev => ({ ...prev, ...updates }))
  }, [])

  const addFilter = useCallback((filterType: keyof SearchQuery['filters'], value: any) => {
    setQuery(prev => ({
      ...prev,
      filters: {
        ...prev.filters,
        [filterType]: Array.isArray(prev.filters[filterType])
          ? [...(prev.filters[filterType] as any[]), value]
          : [value]
      }
    }))
  }, [])

  const removeFilter = useCallback((filterType: keyof SearchQuery['filters'], value?: any) => {
    setQuery(prev => ({
      ...prev,
      filters: {
        ...prev.filters,
        [filterType]: value !== undefined 
          ? (prev.filters[filterType] as any[])?.filter(v => v !== value)
          : undefined
      }
    }))
  }, [])

  return (
    <div className={`advanced-search-interface ${className}`}>
      {/* Search Header */}
      <div className="search-header bg-white border-b border-gray-200 p-4">
        {/* Main Search Bar */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={query.text}
            onChange={(e) => updateQuery({ text: e.target.value })}
            placeholder="Search conversations, messages, and topics..."
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg text-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          
          {/* Quick Suggestions */}
          {suggestions.length > 0 && query.text && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-60 overflow-auto">
              {suggestions.slice(0, 8).map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => updateQuery({ text: suggestion.text })}
                  className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center gap-3"
                >
                  <div className="text-sm">
                    <div className="font-medium">{suggestion.displayText}</div>
                    {suggestion.description && (
                      <div className="text-gray-500">{suggestion.description}</div>
                    )}
                  </div>
                  <div className="text-xs text-gray-400 ml-auto">
                    {suggestion.frequency > 0 && `${suggestion.frequency} matches`}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Search Controls */}
        <div className="flex items-center gap-4">
          {/* Query Type */}
          <select
            value={query.queryType}
            onChange={(e) => updateQuery({ queryType: e.target.value as any })}
            className="px-3 py-2 border border-gray-300 rounded text-sm"
          >
            <option value="keyword">Keyword</option>
            <option value="phrase">Exact Phrase</option>
            <option value="semantic">Semantic</option>
            <option value="fuzzy">Fuzzy</option>
          </select>

          {/* Filters Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-3 py-2 border rounded text-sm ${
              showFilters ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-300'
            }`}
          >
            <Filter className="w-4 h-4" />
            Filters
            <ChevronDown className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
          </button>

          {/* Sort Options */}
          <select
            value={`${query.sorting.field}-${query.sorting.direction}`}
            onChange={(e) => {
              const [field, direction] = e.target.value.split('-')
              updateQuery({ 
                sorting: { 
                  field: field as any, 
                  direction: direction as 'asc' | 'desc' 
                } 
              })
            }}
            className="px-3 py-2 border border-gray-300 rounded text-sm"
          >
            <option value="relevance-desc">Most Relevant</option>
            <option value="date-desc">Newest First</option>
            <option value="date-asc">Oldest First</option>
            <option value="rating-desc">Highest Rated</option>
          </select>
        </div>

        {/* Active Filters */}
        <ActiveFilters 
          filters={query.filters}
          onRemoveFilter={removeFilter}
          className="mt-3"
        />
      </div>

      {/* Search Body */}
      <div className="search-body flex">
        {/* Filters Sidebar */}
        {showFilters && facets && (
          <SearchFiltersSidebar
            facets={facets}
            currentFilters={query.filters}
            onAddFilter={addFilter}
            onRemoveFilter={removeFilter}
            className="w-80 border-r border-gray-200"
          />
        )}

        {/* Results */}
        <div className="flex-1">
          {/* Search Stats */}
          {searchStats && (
            <div className="p-4 bg-gray-50 border-b border-gray-200 text-sm text-gray-600">
              {searchStats.total.toLocaleString()} results 
              ({(searchStats.time / 1000).toFixed(2)} seconds)
            </div>
          )}

          {/* Loading State */}
          {isLoading && (
            <div className="p-8 text-center">
              <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4" />
              <div className="text-gray-600">Searching...</div>
            </div>
          )}

          {/* Results List */}
          {!isLoading && (
            <SearchResultsList
              results={results}
              onResultSelect={onResultSelect}
              query={query.text}
            />
          )}
        </div>
      </div>
    </div>
  )
}

// Active Filters Component
const ActiveFilters: React.FC<{
  filters: SearchQuery['filters']
  onRemoveFilter: (type: keyof SearchQuery['filters'], value?: any) => void
  className?: string
}> = ({ filters, onRemoveFilter, className = '' }) => {
  const activeFilters: Array<{ type: string; value: any; display: string }> = []

  // Build active filters list
  if (filters.agents?.length) {
    filters.agents.forEach(agent => {
      activeFilters.push({ type: 'agents', value: agent, display: `Agent: ${agent}` })
    })
  }

  if (filters.topics?.length) {
    filters.topics.forEach(topic => {
      activeFilters.push({ type: 'topics', value: topic, display: `Topic: ${topic}` })
    })
  }

  if (filters.dateRange) {
    const { start, end } = filters.dateRange
    activeFilters.push({
      type: 'dateRange',
      value: null,
      display: `Date: ${start.toLocaleDateString()} - ${end.toLocaleDateString()}`
    })
  }

  if (activeFilters.length === 0) return null

  return (
    <div className={`active-filters flex flex-wrap gap-2 ${className}`}>
      {activeFilters.map((filter, index) => (
        <span
          key={index}
          className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
        >
          {filter.display}
          <button
            onClick={() => onRemoveFilter(filter.type as any, filter.value)}
            className="hover:bg-blue-200 rounded-full p-0.5"
          >
            <X className="w-3 h-3" />
          </button>
        </span>
      ))}
      <button
        onClick={() => {
          Object.keys(filters).forEach(key => {
            onRemoveFilter(key as any)
          })
        }}
        className="text-sm text-gray-500 hover:text-gray-700 underline"
      >
        Clear all
      </button>
    </div>
  )
}

// Search Results List Component
const SearchResultsList: React.FC<{
  results: SearchResult[]
  onResultSelect: (result: SearchResult) => void
  query: string
}> = ({ results, onResultSelect, query }) => {
  if (results.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500">
        <Search className="w-12 h-12 mx-auto mb-4 text-gray-300" />
        <div className="text-lg mb-2">No results found</div>
        <div className="text-sm">Try different keywords or adjust your filters</div>
      </div>
    )
  }

  return (
    <div className="search-results p-4 space-y-4">
      {results.map((result, index) => (
        <SearchResultCard
          key={result.document.documentId}
          result={result}
          onSelect={() => onResultSelect(result)}
          query={query}
        />
      ))}
    </div>
  )
}

// Individual Search Result Component
const SearchResultCard: React.FC<{
  result: SearchResult
  onSelect: () => void
  query: string
}> = ({ result, onSelect, query }) => {
  const { document, score, highlights } = result

  return (
    <div
      onClick={onSelect}
      className="search-result-card bg-white border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors"
    >
      {/* Result Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <h3 className="font-semibold text-gray-800 mb-1">
            {document.title || 'Untitled'}
          </h3>
          <div className="flex items-center gap-3 text-sm text-gray-500">
            {document.agentName && (
              <span className="flex items-center gap-1">
                <User className="w-3 h-3" />
                {document.agentName}
              </span>
            )}
            <span>{new Date(document.timestamp).toLocaleDateString()}</span>
            <span>{document.wordCount} words</span>
            {document.bookmarked && <Bookmark className="w-3 h-3 text-yellow-500" />}
          </div>
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-500 mb-1">
            Score: {(score * 100).toFixed(0)}%
          </div>
          <div className="flex gap-1">
            {document.topics.slice(0, 2).map(topic => (
              <span key={topic} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                {topic}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Content Preview with Highlights */}
      <div className="text-gray-700 text-sm mb-3">
        {highlights.length > 0 ? (
          <div className="space-y-2">
            {highlights[0].fragments.slice(0, 2).map((fragment, i) => (
              <div key={i} className="bg-yellow-50 p-2 rounded">
                ...{highlightText(fragment, query)}...
              </div>
            ))}
          </div>
        ) : (
          <div>
            {document.summary || document.content.substring(0, 200) + '...'}
          </div>
        )}
      </div>

      {/* Conversation Context */}
      {result.conversationContext && (
        <div className="text-xs text-gray-500 border-t pt-2">
          <div>Context from conversation</div>
        </div>
      )}
    </div>
  )
}

// Helper Functions
function debounce<T extends (...args: any[]) => any>(func: T, wait: number): T {
  let timeout: NodeJS.Timeout
  return ((...args: any[]) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }) as T
}

function highlightText(text: string, query: string): React.ReactNode {
  if (!query) return text
  
  const regex = new RegExp(`(${query})`, 'gi')
  const parts = text.split(regex)
  
  return parts.map((part, i) => 
    regex.test(part) ? (
      <mark key={i} className="bg-yellow-200 px-1 rounded">{part}</mark>
    ) : part
  )
}
```

## 🎯 **Key Takeaways**

1. **Relevance scoring is crucial** - Users expect the best results first
2. **Faceted search improves discovery** - Let users explore data dimensions
3. **Real-time suggestions enhance UX** - Help users formulate better queries
4. **Context matters for results** - Show surrounding conversation for clarity
5. **Performance at scale requires optimization** - Index efficiently and cache results
6. **Search analytics drive improvement** - Track what users search for
7. **Visual highlighting aids comprehension** - Show users why results matched

---

**Next**: [Architecture Deep-Dives](../architecture/01-component-architecture.md) - Technical Design Decisions

**Previous**: [05-conversation-threading.md](./05-conversation-threading.md)