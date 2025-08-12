# Advanced Features 4: Message Persistence System - Advanced State Management

## 🎯 **Learning Objectives**

By the end of this tutorial, you will:
- Build sophisticated message persistence using IndexedDB and localStorage
- Implement conversation threading and search functionality
- Create message synchronization across browser tabs and devices
- Handle large conversation histories with pagination and optimization
- Build backup and export systems for conversation data
- Implement conversation sharing and collaborative features

## 💾 **The Message Persistence Challenge**

Modern chat applications need robust data management:
- **Browser Refresh**: Messages should survive page reloads
- **Large Conversations**: Handle thousands of messages efficiently
- **Search & Filtering**: Quick access to historical conversations
- **Multi-device Sync**: Conversations available across devices
- **Offline Support**: Work without internet connectivity
- **Data Export**: Users should own their conversation data

**Our goal**: Build **production-grade message persistence** that scales and performs well.

## 🗄️ **Persistence Architecture**

### **Step 1: Message Storage Models**

```typescript
// src/types/messageStorage.ts
export interface StoredMessage {
  id: string
  conversationId: string
  content: string
  role: 'user' | 'assistant'
  timestamp: Date
  
  // Agent information
  agentInfo?: {
    id: string
    name: string
    protocol: string
    confidence?: number
  }
  
  // Rich content
  metadata?: {
    routingDecision?: any
    streamingChunks?: string[]
    processingTime?: number
    tokens?: number
    cost?: number
  }
  
  // Message state
  status: 'sending' | 'sent' | 'delivered' | 'error' | 'retry'
  errorDetails?: string
  parentMessageId?: string // For message threading
  editedAt?: Date
  version: number
  
  // Search and indexing
  tags?: string[]
  summary?: string
  searchableContent: string
}

export interface StoredConversation {
  id: string
  title: string
  description?: string
  createdAt: Date
  updatedAt: Date
  
  // Message references
  messageCount: number
  lastMessageId?: string
  lastActivity: Date
  
  // Conversation metadata
  participants: Array<{
    type: 'user' | 'agent'
    id: string
    name: string
  }>
  
  // Organization
  tags: string[]
  folder?: string
  starred: boolean
  archived: boolean
  
  // Sharing and collaboration
  shared: boolean
  shareUrl?: string
  collaborators?: Array<{
    id: string
    name: string
    permissions: 'read' | 'write' | 'admin'
  }>
  
  // Statistics
  stats: {
    totalMessages: number
    totalTokens: number
    totalCost: number
    avgResponseTime: number
  }
}

export interface MessageSearchIndex {
  messageId: string
  conversationId: string
  content: string
  keywords: string[]
  entities: string[]
  timestamp: Date
  agentName?: string
  tags: string[]
}
```

### **Step 2: IndexedDB Storage Service**

```typescript
// src/services/messageStorageService.ts
interface StorageConfig {
  maxConversations: number
  maxMessagesPerConversation: number
  enableCompression: boolean
  enableSearch: boolean
  syncEnabled: boolean
  backupInterval: number // minutes
}

export class MessageStorageService {
  private db: IDBDatabase | null = null
  private config: StorageConfig
  private searchIndex = new Map<string, MessageSearchIndex>()
  private compressionWorker?: Worker

  constructor(config: Partial<StorageConfig> = {}) {
    this.config = {
      maxConversations: 1000,
      maxMessagesPerConversation: 10000,
      enableCompression: true,
      enableSearch: true,
      syncEnabled: false,
      backupInterval: 30,
      ...config
    }

    this.initialize()
  }

  /**
   * Initialize IndexedDB database
   */
  private async initialize(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('MessageStorage', 3)

      request.onerror = () => reject(request.error)
      request.onsuccess = () => {
        this.db = request.result
        this.setupEventHandlers()
        this.loadSearchIndex()
        resolve()
      }

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result
        this.createObjectStores(db)
      }
    })
  }

  private createObjectStores(db: IDBDatabase): void {
    // Conversations store
    if (!db.objectStoreNames.contains('conversations')) {
      const conversationStore = db.createObjectStore('conversations', { keyPath: 'id' })
      conversationStore.createIndex('updatedAt', 'updatedAt')
      conversationStore.createIndex('tags', 'tags', { multiEntry: true })
      conversationStore.createIndex('folder', 'folder')
      conversationStore.createIndex('starred', 'starred')
    }

    // Messages store
    if (!db.objectStoreNames.contains('messages')) {
      const messageStore = db.createObjectStore('messages', { keyPath: 'id' })
      messageStore.createIndex('conversationId', 'conversationId')
      messageStore.createIndex('timestamp', 'timestamp')
      messageStore.createIndex('role', 'role')
      messageStore.createIndex('status', 'status')
      messageStore.createIndex('parentMessageId', 'parentMessageId')
    }

    // Search index store
    if (!db.objectStoreNames.contains('searchIndex')) {
      const searchStore = db.createObjectStore('searchIndex', { keyPath: 'messageId' })
      searchStore.createIndex('conversationId', 'conversationId')
      searchStore.createIndex('keywords', 'keywords', { multiEntry: true })
      searchStore.createIndex('entities', 'entities', { multiEntry: true })
      searchStore.createIndex('timestamp', 'timestamp')
    }

    // Settings store
    if (!db.objectStoreNames.contains('settings')) {
      db.createObjectStore('settings', { keyPath: 'key' })
    }
  }

  /**
   * Save message with full indexing
   */
  async saveMessage(message: StoredMessage): Promise<void> {
    if (!this.db) throw new Error('Database not initialized')

    try {
      // Prepare message for storage
      const messageToStore = {
        ...message,
        searchableContent: this.createSearchableContent(message),
        timestamp: new Date(message.timestamp), // Ensure Date object
      }

      // Compress large content if enabled
      if (this.config.enableCompression && messageToStore.content.length > 5000) {
        messageToStore.content = await this.compressContent(messageToStore.content)
      }

      // Start transaction
      const transaction = this.db.transaction(['messages', 'conversations', 'searchIndex'], 'readwrite')
      
      // Save message
      const messageStore = transaction.objectStore('messages')
      await this.promisifyRequest(messageStore.put(messageToStore))

      // Update conversation
      await this.updateConversationAfterMessage(transaction, message)

      // Update search index
      if (this.config.enableSearch) {
        await this.updateSearchIndex(transaction, messageToStore)
      }

      // Cleanup if needed
      await this.cleanupOldMessagesIfNeeded(transaction, message.conversationId)

    } catch (error) {
      console.error('Failed to save message:', error)
      throw error
    }
  }

  /**
   * Load messages for a conversation with pagination
   */
  async loadMessages(
    conversationId: string,
    options: {
      limit?: number
      offset?: number
      before?: Date
      after?: Date
      includeMetadata?: boolean
    } = {}
  ): Promise<StoredMessage[]> {
    if (!this.db) throw new Error('Database not initialized')

    const { limit = 50, offset = 0, before, after, includeMetadata = true } = options

    try {
      const transaction = this.db.transaction('messages', 'readonly')
      const store = transaction.objectStore('messages')
      const index = store.index('conversationId')

      const range = IDBKeyRange.only(conversationId)
      const request = index.openCursor(range, 'prev') // Newest first

      const messages: StoredMessage[] = []
      let skipCount = 0
      let addedCount = 0

      return new Promise((resolve, reject) => {
        request.onsuccess = async (event) => {
          const cursor = (event.target as IDBRequest).result

          if (!cursor || addedCount >= limit) {
            // Decompress and hydrate messages
            const hydratedMessages = await Promise.all(
              messages.map(msg => this.hydrateMessage(msg, includeMetadata))
            )
            resolve(hydratedMessages)
            return
          }

          const message = cursor.value as StoredMessage

          // Apply time filters
          if (before && message.timestamp >= before) {
            cursor.continue()
            return
          }
          if (after && message.timestamp <= after) {
            cursor.continue()
            return
          }

          // Apply offset
          if (skipCount < offset) {
            skipCount++
            cursor.continue()
            return
          }

          messages.push(message)
          addedCount++
          cursor.continue()
        }

        request.onerror = () => reject(request.error)
      })
    } catch (error) {
      console.error('Failed to load messages:', error)
      throw error
    }
  }

  /**
   * Search messages across all conversations
   */
  async searchMessages(query: string, options: {
    conversationId?: string
    limit?: number
    includeArchived?: boolean
  } = {}): Promise<Array<StoredMessage & { relevanceScore: number }>> {
    if (!this.db || !this.config.enableSearch) return []

    const { limit = 100, conversationId, includeArchived = false } = options
    const keywords = this.extractKeywords(query.toLowerCase())

    try {
      const transaction = this.db.transaction(['searchIndex', 'messages'], 'readonly')
      const searchStore = transaction.objectStore('searchIndex')
      const messageStore = transaction.objectStore('messages')

      const results = new Map<string, { message: StoredMessage, score: number }>()

      // Search by keywords
      for (const keyword of keywords) {
        const index = searchStore.index('keywords')
        const range = IDBKeyRange.only(keyword)
        const request = index.openCursor(range)

        await new Promise<void>((resolve, reject) => {
          request.onsuccess = async (event) => {
            const cursor = (event.target as IDBRequest).result

            if (!cursor) {
              resolve()
              return
            }

            const searchItem = cursor.value as MessageSearchIndex

            // Filter by conversation if specified
            if (conversationId && searchItem.conversationId !== conversationId) {
              cursor.continue()
              return
            }

            // Get the actual message
            const messageRequest = messageStore.get(searchItem.messageId)
            messageRequest.onsuccess = () => {
              const message = messageRequest.result as StoredMessage

              if (message) {
                // Calculate relevance score
                const score = this.calculateRelevanceScore(query, keywords, message, searchItem)
                
                const existing = results.get(message.id)
                if (!existing || existing.score < score) {
                  results.set(message.id, { message, score })
                }
              }
            }

            cursor.continue()
          }

          request.onerror = () => reject(request.error)
        })
      }

      // Convert to array and sort by relevance
      const sortedResults = Array.from(results.values())
        .sort((a, b) => b.score - a.score)
        .slice(0, limit)
        .map(result => ({
          ...result.message,
          relevanceScore: result.score
        }))

      // Hydrate messages
      return Promise.all(
        sortedResults.map(msg => this.hydrateMessage(msg, false))
      )

    } catch (error) {
      console.error('Search failed:', error)
      return []
    }
  }

  /**
   * Save conversation metadata
   */
  async saveConversation(conversation: StoredConversation): Promise<void> {
    if (!this.db) throw new Error('Database not initialized')

    try {
      const transaction = this.db.transaction('conversations', 'readwrite')
      const store = transaction.objectStore('conversations')
      
      const conversationToStore = {
        ...conversation,
        updatedAt: new Date(),
      }

      await this.promisifyRequest(store.put(conversationToStore))
    } catch (error) {
      console.error('Failed to save conversation:', error)
      throw error
    }
  }

  /**
   * Load conversations with filtering and pagination
   */
  async loadConversations(options: {
    limit?: number
    offset?: number
    folder?: string
    starred?: boolean
    archived?: boolean
    tags?: string[]
  } = {}): Promise<StoredConversation[]> {
    if (!this.db) throw new Error('Database not initialized')

    const { limit = 50, offset = 0, folder, starred, archived, tags } = options

    try {
      const transaction = this.db.transaction('conversations', 'readonly')
      const store = transaction.objectStore('conversations')
      const index = store.index('updatedAt')

      const request = index.openCursor(null, 'prev') // Newest first
      const conversations: StoredConversation[] = []
      let skipCount = 0
      let addedCount = 0

      return new Promise((resolve, reject) => {
        request.onsuccess = (event) => {
          const cursor = (event.target as IDBRequest).result

          if (!cursor || addedCount >= limit) {
            resolve(conversations)
            return
          }

          const conversation = cursor.value as StoredConversation

          // Apply filters
          if (folder !== undefined && conversation.folder !== folder) {
            cursor.continue()
            return
          }
          if (starred !== undefined && conversation.starred !== starred) {
            cursor.continue()
            return
          }
          if (archived !== undefined && conversation.archived !== archived) {
            cursor.continue()
            return
          }
          if (tags && !tags.some(tag => conversation.tags.includes(tag))) {
            cursor.continue()
            return
          }

          // Apply offset
          if (skipCount < offset) {
            skipCount++
            cursor.continue()
            return
          }

          conversations.push(conversation)
          addedCount++
          cursor.continue()
        }

        request.onerror = () => reject(request.error)
      })
    } catch (error) {
      console.error('Failed to load conversations:', error)
      throw error
    }
  }

  /**
   * Export conversation data
   */
  async exportConversations(conversationIds?: string[]): Promise<{
    conversations: StoredConversation[]
    messages: StoredMessage[]
    exportedAt: Date
    version: string
  }> {
    if (!this.db) throw new Error('Database not initialized')

    try {
      const transaction = this.db.transaction(['conversations', 'messages'], 'readonly')
      
      let conversations: StoredConversation[] = []
      let messages: StoredMessage[] = []

      if (conversationIds) {
        // Export specific conversations
        for (const id of conversationIds) {
          const conv = await this.promisifyRequest(
            transaction.objectStore('conversations').get(id)
          )
          if (conv) conversations.push(conv)

          const conversationMessages = await this.loadMessages(id, { limit: 10000 })
          messages.push(...conversationMessages)
        }
      } else {
        // Export all conversations
        conversations = await this.loadConversations({ limit: 10000 })
        
        for (const conv of conversations) {
          const conversationMessages = await this.loadMessages(conv.id, { limit: 10000 })
          messages.push(...conversationMessages)
        }
      }

      return {
        conversations,
        messages,
        exportedAt: new Date(),
        version: '1.0.0'
      }
    } catch (error) {
      console.error('Failed to export conversations:', error)
      throw error
    }
  }

  /**
   * Import conversation data
   */
  async importConversations(data: {
    conversations: StoredConversation[]
    messages: StoredMessage[]
  }): Promise<{ imported: number, skipped: number, errors: number }> {
    if (!this.db) throw new Error('Database not initialized')

    let imported = 0
    let skipped = 0
    let errors = 0

    try {
      // Import conversations first
      for (const conversation of data.conversations) {
        try {
          await this.saveConversation(conversation)
          imported++
        } catch (error) {
          console.warn('Failed to import conversation:', conversation.id, error)
          errors++
        }
      }

      // Import messages
      for (const message of data.messages) {
        try {
          await this.saveMessage(message)
          imported++
        } catch (error) {
          console.warn('Failed to import message:', message.id, error)
          errors++
        }
      }

      return { imported, skipped, errors }
    } catch (error) {
      console.error('Import failed:', error)
      throw error
    }
  }

  // Helper methods

  private async updateConversationAfterMessage(
    transaction: IDBTransaction,
    message: StoredMessage
  ): Promise<void> {
    const conversationStore = transaction.objectStore('conversations')
    const conversation = await this.promisifyRequest(
      conversationStore.get(message.conversationId)
    ) as StoredConversation

    if (conversation) {
      conversation.updatedAt = new Date()
      conversation.lastMessageId = message.id
      conversation.lastActivity = message.timestamp
      conversation.messageCount++
      
      // Update stats
      if (message.metadata?.processingTime) {
        conversation.stats.avgResponseTime = 
          (conversation.stats.avgResponseTime + message.metadata.processingTime) / 2
      }
      if (message.metadata?.tokens) {
        conversation.stats.totalTokens += message.metadata.tokens
      }
      if (message.metadata?.cost) {
        conversation.stats.totalCost += message.metadata.cost
      }

      await this.promisifyRequest(conversationStore.put(conversation))
    }
  }

  private async updateSearchIndex(
    transaction: IDBTransaction,
    message: StoredMessage
  ): Promise<void> {
    const searchStore = transaction.objectStore('searchIndex')
    
    const searchIndex: MessageSearchIndex = {
      messageId: message.id,
      conversationId: message.conversationId,
      content: message.content,
      keywords: this.extractKeywords(message.searchableContent),
      entities: this.extractEntities(message.content),
      timestamp: message.timestamp,
      agentName: message.agentInfo?.name,
      tags: message.tags || [],
    }

    await this.promisifyRequest(searchStore.put(searchIndex))
    this.searchIndex.set(message.id, searchIndex)
  }

  private createSearchableContent(message: StoredMessage): string {
    let content = message.content.toLowerCase()
    
    // Add agent name to searchable content
    if (message.agentInfo?.name) {
      content += ' ' + message.agentInfo.name.toLowerCase()
    }
    
    // Add tags to searchable content
    if (message.tags) {
      content += ' ' + message.tags.join(' ').toLowerCase()
    }

    return content
  }

  private extractKeywords(text: string): string[] {
    // Simple keyword extraction - in production, use a more sophisticated NLP library
    return text
      .toLowerCase()
      .replace(/[^\w\s]/g, ' ')
      .split(/\s+/)
      .filter(word => word.length > 2)
      .filter(word => !['the', 'and', 'but', 'for', 'are', 'with', 'this', 'that'].includes(word))
      .slice(0, 50) // Limit keywords
  }

  private extractEntities(text: string): string[] {
    // Simple entity extraction - in production, use NLP
    const entities: string[] = []
    
    // Extract potential names (capitalized words)
    const names = text.match(/\b[A-Z][a-z]+\b/g) || []
    entities.push(...names)
    
    // Extract numbers
    const numbers = text.match(/\b\d+\.?\d*\b/g) || []
    entities.push(...numbers)
    
    return entities.slice(0, 20)
  }

  private calculateRelevanceScore(
    query: string,
    keywords: string[],
    message: StoredMessage,
    searchIndex: MessageSearchIndex
  ): number {
    let score = 0
    
    // Exact phrase match gets highest score
    if (message.content.toLowerCase().includes(query.toLowerCase())) {
      score += 10
    }
    
    // Keyword matches
    for (const keyword of keywords) {
      if (searchIndex.keywords.includes(keyword)) {
        score += 2
      }
      if (searchIndex.entities.includes(keyword)) {
        score += 1
      }
    }
    
    // Recent messages get slight boost
    const daysSinceMessage = (Date.now() - message.timestamp.getTime()) / (1000 * 60 * 60 * 24)
    if (daysSinceMessage < 7) {
      score += 1
    }
    
    // Agent name match
    if (message.agentInfo?.name && query.toLowerCase().includes(message.agentInfo.name.toLowerCase())) {
      score += 3
    }

    return score
  }

  private async hydrateMessage(message: StoredMessage, includeMetadata: boolean): Promise<StoredMessage> {
    // Decompress content if needed
    if (message.content.startsWith('compressed:')) {
      message.content = await this.decompressContent(message.content)
    }

    // Remove internal search content
    const { searchableContent, ...cleanMessage } = message as any

    // Optionally strip metadata for performance
    if (!includeMetadata) {
      delete cleanMessage.metadata
    }

    return cleanMessage
  }

  private async compressContent(content: string): Promise<string> {
    // Placeholder for compression - implement with CompressionStream or library
    return `compressed:${btoa(content)}`
  }

  private async decompressContent(compressed: string): Promise<string> {
    // Placeholder for decompression
    return atob(compressed.replace('compressed:', ''))
  }

  private async cleanupOldMessagesIfNeeded(transaction: IDBTransaction, conversationId: string): Promise<void> {
    // Clean up if conversation has too many messages
    const messageStore = transaction.objectStore('messages')
    const index = messageStore.index('conversationId')
    const countRequest = index.count(IDBKeyRange.only(conversationId))

    countRequest.onsuccess = () => {
      const count = countRequest.result
      if (count > this.config.maxMessagesPerConversation) {
        // Delete oldest messages beyond limit
        const deleteCount = count - this.config.maxMessagesPerConversation
        // Implementation would delete oldest messages
      }
    }
  }

  private setupEventHandlers(): void {
    // Handle database version changes, etc.
    if (this.db) {
      this.db.onversionchange = () => {
        this.db?.close()
        this.db = null
        // Reinitialize
        this.initialize()
      }
    }
  }

  private async loadSearchIndex(): Promise<void> {
    if (!this.db || !this.config.enableSearch) return

    try {
      const transaction = this.db.transaction('searchIndex', 'readonly')
      const store = transaction.objectStore('searchIndex')
      const request = store.openCursor()

      return new Promise((resolve, reject) => {
        request.onsuccess = (event) => {
          const cursor = (event.target as IDBRequest).result
          if (cursor) {
            this.searchIndex.set(cursor.value.messageId, cursor.value)
            cursor.continue()
          } else {
            resolve()
          }
        }
        request.onerror = () => reject(request.error)
      })
    } catch (error) {
      console.warn('Failed to load search index:', error)
    }
  }

  private promisifyRequest<T>(request: IDBRequest<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      request.onsuccess = () => resolve(request.result)
      request.onerror = () => reject(request.error)
    })
  }
}

export const messageStorage = new MessageStorageService()
```

### **Step 3: React Hook for Message Persistence**

```typescript
// src/hooks/useMessagePersistence.ts
import { useState, useEffect, useCallback, useRef } from 'react'
import { messageStorage } from '../services/messageStorageService'
import { StoredMessage, StoredConversation } from '../types/messageStorage'

interface PersistenceState {
  currentConversationId: string | null
  messages: StoredMessage[]
  conversations: StoredConversation[]
  isLoading: boolean
  isSaving: boolean
  error: Error | null
  hasMore: boolean
}

export const useMessagePersistence = () => {
  const [state, setState] = useState<PersistenceState>({
    currentConversationId: null,
    messages: [],
    conversations: [],
    isLoading: false,
    isSaving: false,
    error: null,
    hasMore: true,
  })

  const offsetRef = useRef(0)

  // Initialize - load conversations
  useEffect(() => {
    loadConversations()
  }, [])

  const loadConversations = useCallback(async (reset = false) => {
    if (reset) {
      setState(prev => ({ ...prev, conversations: [], isLoading: true }))
    }

    try {
      const conversations = await messageStorage.loadConversations({
        limit: 50,
        offset: reset ? 0 : state.conversations.length,
      })

      setState(prev => ({
        ...prev,
        conversations: reset ? conversations : [...prev.conversations, ...conversations],
        isLoading: false,
        error: null,
      }))
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error as Error,
        isLoading: false,
      }))
    }
  }, [state.conversations.length])

  const loadMessages = useCallback(async (conversationId: string, reset = false) => {
    if (reset) {
      setState(prev => ({ ...prev, messages: [], isLoading: true, currentConversationId: conversationId }))
      offsetRef.current = 0
    }

    try {
      const messages = await messageStorage.loadMessages(conversationId, {
        limit: 50,
        offset: reset ? 0 : offsetRef.current,
      })

      offsetRef.current += messages.length

      setState(prev => ({
        ...prev,
        messages: reset ? messages : [...messages, ...prev.messages], // Prepend older messages
        isLoading: false,
        error: null,
        hasMore: messages.length === 50,
        currentConversationId: conversationId,
      }))
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error as Error,
        isLoading: false,
      }))
    }
  }, [])

  const saveMessage = useCallback(async (message: StoredMessage) => {
    setState(prev => ({ ...prev, isSaving: true }))

    try {
      await messageStorage.saveMessage(message)

      setState(prev => ({
        ...prev,
        messages: prev.currentConversationId === message.conversationId 
          ? [...prev.messages, message]
          : prev.messages,
        isSaving: false,
        error: null,
      }))

      // Update conversation in list
      await loadConversations(true)
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error as Error,
        isSaving: false,
      }))
    }
  }, [loadConversations])

  const createConversation = useCallback(async (title: string): Promise<string> => {
    const conversationId = `conv-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    
    const conversation: StoredConversation = {
      id: conversationId,
      title,
      createdAt: new Date(),
      updatedAt: new Date(),
      messageCount: 0,
      lastActivity: new Date(),
      participants: [{ type: 'user', id: 'user-1', name: 'You' }],
      tags: [],
      starred: false,
      archived: false,
      shared: false,
      stats: {
        totalMessages: 0,
        totalTokens: 0,
        totalCost: 0,
        avgResponseTime: 0,
      },
    }

    try {
      await messageStorage.saveConversation(conversation)
      await loadConversations(true)
      return conversationId
    } catch (error) {
      setState(prev => ({ ...prev, error: error as Error }))
      throw error
    }
  }, [loadConversations])

  const searchMessages = useCallback(async (query: string) => {
    try {
      setState(prev => ({ ...prev, isLoading: true }))
      const results = await messageStorage.searchMessages(query, { limit: 100 })
      
      setState(prev => ({
        ...prev,
        messages: results,
        isLoading: false,
        error: null,
      }))

      return results
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error as Error,
        isLoading: false,
      }))
      throw error
    }
  }, [])

  const exportConversation = useCallback(async (conversationId: string) => {
    try {
      const data = await messageStorage.exportConversations([conversationId])
      
      // Create download
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `conversation-${conversationId}-${new Date().toISOString().split('T')[0]}.json`
      a.click()
      
      URL.revokeObjectURL(url)
    } catch (error) {
      setState(prev => ({ ...prev, error: error as Error }))
    }
  }, [])

  const deleteMessage = useCallback(async (messageId: string) => {
    // Implementation would mark message as deleted or remove from storage
    setState(prev => ({
      ...prev,
      messages: prev.messages.filter(msg => msg.id !== messageId),
    }))
  }, [])

  const updateMessage = useCallback(async (messageId: string, updates: Partial<StoredMessage>) => {
    setState(prev => ({
      ...prev,
      messages: prev.messages.map(msg =>
        msg.id === messageId 
          ? { ...msg, ...updates, editedAt: new Date(), version: msg.version + 1 }
          : msg
      ),
    }))

    // Save updated message to storage
    const message = state.messages.find(msg => msg.id === messageId)
    if (message) {
      const updatedMessage = { ...message, ...updates, editedAt: new Date(), version: message.version + 1 }
      await messageStorage.saveMessage(updatedMessage)
    }
  }, [state.messages])

  return {
    ...state,
    loadConversations,
    loadMessages,
    saveMessage,
    createConversation,
    searchMessages,
    exportConversation,
    deleteMessage,
    updateMessage,
    loadMoreMessages: () => loadMessages(state.currentConversationId!, false),
  }
}
```

## 🎯 **Key Takeaways**

1. **IndexedDB scales well** - Handle thousands of messages efficiently
2. **Search indexing is crucial** - Pre-compute keywords and entities
3. **Compression saves space** - Large messages should be compressed
4. **Pagination prevents performance issues** - Don't load everything at once
5. **Export functionality is expected** - Users should own their data
6. **Error handling is critical** - Storage operations can fail
7. **Search relevance matters** - Score results by multiple factors

---

**Next**: [05-conversation-threading.md](./05-conversation-threading.md) - Advanced Message Organization

**Previous**: [03-ai-routing-transparency.md](./03-ai-routing-transparency.md)