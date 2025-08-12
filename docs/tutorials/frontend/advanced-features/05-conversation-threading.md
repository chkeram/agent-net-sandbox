# Advanced Features 5: Conversation Threading - Advanced Message Organization

## 🎯 **Learning Objectives**

By the end of this tutorial, you will:
- Build sophisticated conversation threading and branching systems
- Implement message reply chains and nested conversations
- Create topic-based conversation organization and tagging
- Handle conversation merging and splitting operations
- Build visual thread navigation and tree-view displays
- Implement conversation search and filtering across threads

## 🧵 **The Conversation Threading Challenge**

Complex conversations need advanced organization:
- **Branching Conversations**: Multiple discussion threads from one message
- **Topic Tracking**: Organize messages by subject matter
- **Reply Chains**: Thread messages that respond to specific points
- **Context Management**: Maintain conversation context across branches
- **Visual Navigation**: Help users follow complex discussion flows
- **Search Across Threads**: Find messages in specific conversation branches

**Our goal**: Build **intuitive conversation threading** that scales to complex multi-topic discussions.

## 🌳 **Threading Architecture**

### **Step 1: Thread Data Models**

```typescript
// src/types/conversationThreading.ts
export interface ConversationThread {
  id: string
  conversationId: string
  parentThreadId?: string
  
  // Thread metadata
  title: string
  topic?: string
  summary?: string
  tags: string[]
  
  // Thread structure
  rootMessageId: string
  messageIds: string[]
  branchPoints: string[] // Message IDs where this thread branches
  
  // Thread state
  status: 'active' | 'resolved' | 'archived' | 'merged'
  participants: ThreadParticipant[]
  
  // Timestamps
  createdAt: Date
  updatedAt: Date
  lastActivity: Date
  
  // Threading metadata
  depth: number // How deep in the thread tree
  messageCount: number
  branchCount: number
  
  // Visual properties
  color?: string
  collapsed: boolean
}

export interface ThreadedMessage extends StoredMessage {
  // Thread relationships
  threadId: string
  parentMessageId?: string
  childMessageIds: string[]
  replyToMessageId?: string
  
  // Thread position
  threadPosition: number
  depth: number
  
  // Topic classification
  topics: string[]
  topicConfidence: Record<string, number>
  
  // Threading metadata
  branchesFromHere: string[] // Thread IDs that branch from this message
  mentionedMessageIds: string[]
}

export interface ThreadParticipant {
  type: 'user' | 'agent'
  id: string
  name: string
  joinedAt: Date
  lastActiveAt: Date
  messageCount: number
  role?: 'creator' | 'active' | 'observer'
}

export interface ConversationBranch {
  id: string
  fromMessageId: string
  toThreadId: string
  branchReason: 'topic_change' | 'followup_question' | 'manual_branch' | 'agent_switch'
  createdAt: Date
  title?: string
}

export interface TopicCluster {
  id: string
  name: string
  keywords: string[]
  messageIds: string[]
  threadIds: string[]
  confidence: number
  representativeMessageId: string
  createdAt: Date
  updatedAt: Date
}
```

### **Step 2: Thread Management Service**

```typescript
// src/services/conversationThreadingService.ts
interface ThreadingConfig {
  maxThreadDepth: number
  autoTopicDetection: boolean
  branchThreshold: number // Similarity threshold for auto-branching
  enableTopicClustering: boolean
  topicModelEndpoint?: string
}

export class ConversationThreadingService {
  private config: ThreadingConfig
  private topicModel?: any // ML model for topic detection
  private threads = new Map<string, ConversationThread>()
  private topicClusters = new Map<string, TopicCluster>()

  constructor(config: Partial<ThreadingConfig> = {}) {
    this.config = {
      maxThreadDepth: 10,
      autoTopicDetection: true,
      branchThreshold: 0.7,
      enableTopicClustering: true,
      ...config
    }

    if (this.config.autoTopicDetection) {
      this.initializeTopicModel()
    }
  }

  /**
   * Create a new conversation thread
   */
  async createThread(params: {
    conversationId: string
    rootMessageId: string
    title: string
    parentThreadId?: string
    topic?: string
    tags?: string[]
  }): Promise<ConversationThread> {
    const { conversationId, rootMessageId, title, parentThreadId, topic, tags = [] } = params

    const threadId = `thread-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    const parentThread = parentThreadId ? this.threads.get(parentThreadId) : undefined
    
    const thread: ConversationThread = {
      id: threadId,
      conversationId,
      parentThreadId,
      title,
      topic,
      tags,
      rootMessageId,
      messageIds: [rootMessageId],
      branchPoints: [],
      status: 'active',
      participants: [],
      createdAt: new Date(),
      updatedAt: new Date(),
      lastActivity: new Date(),
      depth: parentThread ? parentThread.depth + 1 : 0,
      messageCount: 1,
      branchCount: 0,
      collapsed: false,
    }

    this.threads.set(threadId, thread)
    
    // Update parent thread if exists
    if (parentThread) {
      parentThread.branchCount++
      parentThread.branchPoints.push(rootMessageId)
      parentThread.updatedAt = new Date()
    }

    // Auto-detect topic if enabled
    if (this.config.autoTopicDetection && !topic) {
      thread.topic = await this.detectTopicFromMessage(rootMessageId)
    }

    // Update topic clusters
    if (this.config.enableTopicClustering) {
      await this.updateTopicClusters(thread)
    }

    return thread
  }

  /**
   * Add message to thread with intelligent positioning
   */
  async addMessageToThread(
    messageId: string,
    threadId: string,
    options: {
      parentMessageId?: string
      replyToMessageId?: string
      topics?: string[]
      autoCreateBranch?: boolean
    } = {}
  ): Promise<{ thread: ConversationThread, branched?: ConversationThread }> {
    const { parentMessageId, replyToMessageId, topics, autoCreateBranch = true } = options
    
    const thread = this.threads.get(threadId)
    if (!thread) {
      throw new Error(`Thread not found: ${threadId}`)
    }

    // Check if this message should create a new branch
    let branchedThread: ConversationThread | undefined
    if (autoCreateBranch && topics && topics.length > 0) {
      const shouldBranch = await this.shouldCreateBranch(messageId, thread, topics)
      if (shouldBranch) {
        branchedThread = await this.createBranchFromMessage(messageId, thread, topics[0])
        return { thread, branched: branchedThread }
      }
    }

    // Add message to existing thread
    thread.messageIds.push(messageId)
    thread.messageCount++
    thread.updatedAt = new Date()
    thread.lastActivity = new Date()

    // Update topic information
    if (topics) {
      await this.updateThreadTopics(thread, topics)
    }

    return { thread }
  }

  /**
   * Create branch from existing message
   */
  async createBranchFromMessage(
    messageId: string,
    parentThread: ConversationThread,
    newTopic: string
  ): Promise<ConversationThread> {
    if (parentThread.depth >= this.config.maxThreadDepth) {
      throw new Error('Maximum thread depth reached')
    }

    const branchTitle = `Branch: ${newTopic}`
    const branchThread = await this.createThread({
      conversationId: parentThread.conversationId,
      rootMessageId: messageId,
      title: branchTitle,
      parentThreadId: parentThread.id,
      topic: newTopic,
    })

    // Create branch record
    const branch: ConversationBranch = {
      id: `branch-${Date.now()}`,
      fromMessageId: messageId,
      toThreadId: branchThread.id,
      branchReason: 'topic_change',
      createdAt: new Date(),
      title: branchTitle,
    }

    // Remove message from parent thread and add to branch
    parentThread.messageIds = parentThread.messageIds.filter(id => id !== messageId)
    parentThread.messageCount--
    parentThread.branchPoints.push(messageId)

    return branchThread
  }

  /**
   * Merge threads back together
   */
  async mergeThreads(sourceThreadId: string, targetThreadId: string): Promise<ConversationThread> {
    const sourceThread = this.threads.get(sourceThreadId)
    const targetThread = this.threads.get(targetThreadId)

    if (!sourceThread || !targetThread) {
      throw new Error('Thread not found for merge operation')
    }

    if (sourceThread.conversationId !== targetThread.conversationId) {
      throw new Error('Cannot merge threads from different conversations')
    }

    // Merge messages
    targetThread.messageIds.push(...sourceThread.messageIds)
    targetThread.messageCount += sourceThread.messageCount
    targetThread.branchCount += sourceThread.branchCount

    // Merge topics and tags
    if (sourceThread.topic && !targetThread.tags.includes(sourceThread.topic)) {
      targetThread.tags.push(sourceThread.topic)
    }
    targetThread.tags.push(...sourceThread.tags.filter(tag => !targetThread.tags.includes(tag)))

    // Update participants
    for (const participant of sourceThread.participants) {
      const existing = targetThread.participants.find(p => p.id === participant.id)
      if (existing) {
        existing.messageCount += participant.messageCount
        existing.lastActiveAt = participant.lastActiveAt > existing.lastActiveAt 
          ? participant.lastActiveAt 
          : existing.lastActiveAt
      } else {
        targetThread.participants.push(participant)
      }
    }

    // Mark source thread as merged
    sourceThread.status = 'merged'
    targetThread.updatedAt = new Date()

    return targetThread
  }

  /**
   * Get thread hierarchy for visualization
   */
  getThreadHierarchy(conversationId: string): ThreadHierarchy {
    const conversationThreads = Array.from(this.threads.values())
      .filter(thread => thread.conversationId === conversationId)

    const rootThreads = conversationThreads.filter(thread => !thread.parentThreadId)
    
    const buildHierarchy = (thread: ConversationThread): ThreadNode => ({
      thread,
      children: conversationThreads
        .filter(t => t.parentThreadId === thread.id)
        .map(buildHierarchy)
        .sort((a, b) => a.thread.createdAt.getTime() - b.thread.createdAt.getTime())
    })

    return {
      conversationId,
      rootThreads: rootThreads
        .map(buildHierarchy)
        .sort((a, b) => a.thread.createdAt.getTime() - b.thread.createdAt.getTime()),
      totalThreads: conversationThreads.length,
      maxDepth: Math.max(...conversationThreads.map(t => t.depth), 0),
    }
  }

  /**
   * Search messages within specific threads
   */
  async searchInThreads(
    query: string,
    options: {
      threadIds?: string[]
      conversationId?: string
      topic?: string
      includeArchived?: boolean
    } = {}
  ): Promise<ThreadSearchResult[]> {
    const { threadIds, conversationId, topic, includeArchived = false } = options

    let targetThreads = Array.from(this.threads.values())

    // Filter by conversation
    if (conversationId) {
      targetThreads = targetThreads.filter(t => t.conversationId === conversationId)
    }

    // Filter by specific threads
    if (threadIds) {
      targetThreads = targetThreads.filter(t => threadIds.includes(t.id))
    }

    // Filter by topic
    if (topic) {
      targetThreads = targetThreads.filter(t => 
        t.topic === topic || t.tags.includes(topic)
      )
    }

    // Filter by status
    if (!includeArchived) {
      targetThreads = targetThreads.filter(t => t.status !== 'archived')
    }

    // Search within each thread
    const results: ThreadSearchResult[] = []
    
    for (const thread of targetThreads) {
      const threadMessages = await this.getThreadMessages(thread.id)
      const matchingMessages = threadMessages.filter(msg =>
        msg.content.toLowerCase().includes(query.toLowerCase()) ||
        msg.topics?.some(topic => topic.toLowerCase().includes(query.toLowerCase()))
      )

      if (matchingMessages.length > 0) {
        results.push({
          thread,
          messages: matchingMessages,
          matchCount: matchingMessages.length,
          relevanceScore: this.calculateThreadRelevance(query, thread, matchingMessages),
        })
      }
    }

    return results.sort((a, b) => b.relevanceScore - a.relevanceScore)
  }

  /**
   * Detect topic from message content
   */
  private async detectTopicFromMessage(messageId: string): Promise<string | undefined> {
    if (!this.topicModel) return undefined

    try {
      // Get message content
      const message = await messageStorage.loadMessages('', { 
        limit: 1, 
        // This would need to be implemented to get specific message
      })
      
      if (message.length === 0) return undefined

      // Use topic model to classify
      const topics = await this.topicModel.classify(message[0].content)
      return topics.length > 0 ? topics[0].label : undefined
    } catch (error) {
      console.warn('Topic detection failed:', error)
      return undefined
    }
  }

  /**
   * Determine if a message should create a new branch
   */
  private async shouldCreateBranch(
    messageId: string,
    thread: ConversationThread,
    messageTopics: string[]
  ): Promise<boolean> {
    // Don't branch if we're already deep
    if (thread.depth >= this.config.maxThreadDepth - 1) {
      return false
    }

    // Don't branch if thread has few messages
    if (thread.messageCount < 3) {
      return false
    }

    // Check topic similarity with thread
    if (thread.topic) {
      const similarity = this.calculateTopicSimilarity(messageTopics, [thread.topic])
      if (similarity < this.config.branchThreshold) {
        return true
      }
    }

    // Check recent message topics
    const recentMessages = await this.getRecentThreadMessages(thread.id, 3)
    const recentTopics = recentMessages.flatMap(msg => msg.topics || [])
    
    if (recentTopics.length > 0) {
      const similarity = this.calculateTopicSimilarity(messageTopics, recentTopics)
      if (similarity < this.config.branchThreshold) {
        return true
      }
    }

    return false
  }

  private calculateTopicSimilarity(topics1: string[], topics2: string[]): number {
    if (topics1.length === 0 || topics2.length === 0) return 0

    const intersection = topics1.filter(topic => 
      topics2.some(t => t.toLowerCase() === topic.toLowerCase())
    )

    const union = [...new Set([...topics1, ...topics2])]
    
    return intersection.length / union.length
  }

  private async updateThreadTopics(thread: ConversationThread, newTopics: string[]): Promise<void> {
    // Update thread tags with new topics
    for (const topic of newTopics) {
      if (!thread.tags.includes(topic)) {
        thread.tags.push(topic)
      }
    }

    // Update primary topic if not set
    if (!thread.topic && newTopics.length > 0) {
      thread.topic = newTopics[0]
    }
  }

  private async updateTopicClusters(thread: ConversationThread): Promise<void> {
    if (!this.config.enableTopicClustering || !thread.topic) return

    // Find or create topic cluster
    let cluster = Array.from(this.topicClusters.values())
      .find(cluster => cluster.name.toLowerCase() === thread.topic!.toLowerCase())

    if (!cluster) {
      cluster = {
        id: `cluster-${Date.now()}`,
        name: thread.topic,
        keywords: [thread.topic],
        messageIds: [],
        threadIds: [thread.id],
        confidence: 0.8,
        representativeMessageId: thread.rootMessageId,
        createdAt: new Date(),
        updatedAt: new Date(),
      }
      this.topicClusters.set(cluster.id, cluster)
    } else {
      cluster.threadIds.push(thread.id)
      cluster.updatedAt = new Date()
    }
  }

  private async getThreadMessages(threadId: string): Promise<ThreadedMessage[]> {
    const thread = this.threads.get(threadId)
    if (!thread) return []

    // This would integrate with the message storage service
    // to load messages by IDs and convert to ThreadedMessage format
    return []
  }

  private async getRecentThreadMessages(threadId: string, count: number): Promise<ThreadedMessage[]> {
    const messages = await this.getThreadMessages(threadId)
    return messages.slice(-count)
  }

  private calculateThreadRelevance(
    query: string,
    thread: ConversationThread,
    matchingMessages: ThreadedMessage[]
  ): number {
    let score = 0

    // Base score from number of matches
    score += matchingMessages.length * 2

    // Boost for recent activity
    const daysSinceActivity = (Date.now() - thread.lastActivity.getTime()) / (1000 * 60 * 60 * 24)
    if (daysSinceActivity < 7) {
      score += 3
    }

    // Boost for topic match
    if (thread.topic && query.toLowerCase().includes(thread.topic.toLowerCase())) {
      score += 5
    }

    // Boost for tag match
    for (const tag of thread.tags) {
      if (query.toLowerCase().includes(tag.toLowerCase())) {
        score += 2
      }
    }

    return score
  }

  private async initializeTopicModel(): Promise<void> {
    // Initialize topic classification model
    // This would load a pre-trained model or connect to an API
    if (this.config.topicModelEndpoint) {
      // Load from API endpoint
    } else {
      // Use simple keyword-based classification
      this.topicModel = {
        classify: (text: string) => {
          const topics = this.extractTopicsFromText(text)
          return Promise.resolve(topics.map(topic => ({ label: topic, confidence: 0.8 })))
        }
      }
    }
  }

  private extractTopicsFromText(text: string): string[] {
    // Simple topic extraction based on keywords
    const topicKeywords = {
      'technology': ['code', 'programming', 'software', 'computer', 'tech'],
      'math': ['calculate', 'equation', 'number', 'formula', 'mathematics'],
      'science': ['research', 'experiment', 'study', 'analysis', 'hypothesis'],
      'business': ['meeting', 'strategy', 'profit', 'market', 'customer'],
      'personal': ['feel', 'think', 'opinion', 'believe', 'experience'],
    }

    const lowercaseText = text.toLowerCase()
    const detectedTopics: string[] = []

    for (const [topic, keywords] of Object.entries(topicKeywords)) {
      if (keywords.some(keyword => lowercaseText.includes(keyword))) {
        detectedTopics.push(topic)
      }
    }

    return detectedTopics
  }
}

// Supporting types
interface ThreadHierarchy {
  conversationId: string
  rootThreads: ThreadNode[]
  totalThreads: number
  maxDepth: number
}

interface ThreadNode {
  thread: ConversationThread
  children: ThreadNode[]
}

interface ThreadSearchResult {
  thread: ConversationThread
  messages: ThreadedMessage[]
  matchCount: number
  relevanceScore: number
}

export const conversationThreading = new ConversationThreadingService()
```

### **Step 3: Thread Visualization Component**

```typescript
// src/components/ConversationThreadView.tsx
import React, { useState, useCallback } from 'react'
import { ChevronDown, ChevronRight, MessageCircle, GitBranch, Search, Tag, Archive, Merge } from 'lucide-react'
import { ConversationThread, ThreadHierarchy, ThreadNode } from '../types/conversationThreading'

interface ConversationThreadViewProps {
  hierarchy: ThreadHierarchy
  activeThreadId?: string
  onThreadSelect: (threadId: string) => void
  onThreadCreate: (parentThreadId?: string) => void
  onThreadMerge: (sourceId: string, targetId: string) => void
  className?: string
}

export const ConversationThreadView: React.FC<ConversationThreadViewProps> = ({
  hierarchy,
  activeThreadId,
  onThreadSelect,
  onThreadCreate,
  onThreadMerge,
  className = '',
}) => {
  const [expandedThreads, setExpandedThreads] = useState<Set<string>>(new Set())
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedThreads, setSelectedThreads] = useState<Set<string>>(new Set())
  const [showMergeMode, setShowMergeMode] = useState(false)

  const toggleExpanded = useCallback((threadId: string) => {
    setExpandedThreads(prev => {
      const newSet = new Set(prev)
      if (newSet.has(threadId)) {
        newSet.delete(threadId)
      } else {
        newSet.add(threadId)
      }
      return newSet
    })
  }, [])

  const handleThreadSelect = useCallback((threadId: string) => {
    if (showMergeMode) {
      setSelectedThreads(prev => {
        const newSet = new Set(prev)
        if (newSet.has(threadId)) {
          newSet.delete(threadId)
        } else {
          newSet.add(threadId)
        }
        return newSet
      })
    } else {
      onThreadSelect(threadId)
    }
  }, [showMergeMode, onThreadSelect])

  const handleMergeThreads = useCallback(() => {
    const threadIds = Array.from(selectedThreads)
    if (threadIds.length === 2) {
      onThreadMerge(threadIds[0], threadIds[1])
      setSelectedThreads(new Set())
      setShowMergeMode(false)
    }
  }, [selectedThreads, onThreadMerge])

  const filteredRootThreads = searchQuery
    ? hierarchy.rootThreads.filter(node =>
        searchInNode(node, searchQuery.toLowerCase())
      )
    : hierarchy.rootThreads

  return (
    <div className={`conversation-thread-view bg-gray-50 border-r border-gray-200 ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-800">Conversation Threads</h3>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowMergeMode(!showMergeMode)}
              className={`p-2 rounded hover:bg-gray-100 ${showMergeMode ? 'bg-blue-100 text-blue-600' : 'text-gray-500'}`}
              title="Merge threads"
            >
              <Merge className="w-4 h-4" />
            </button>
            <button
              onClick={() => onThreadCreate()}
              className="p-2 text-gray-500 hover:bg-gray-100 rounded"
              title="New thread"
            >
              <MessageCircle className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search threads..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Merge mode controls */}
        {showMergeMode && (
          <div className="mt-3 p-2 bg-blue-50 rounded border border-blue-200">
            <div className="text-sm text-blue-800 mb-2">
              Select 2 threads to merge ({selectedThreads.size}/2)
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleMergeThreads}
                disabled={selectedThreads.size !== 2}
                className="px-3 py-1 bg-blue-600 text-white text-sm rounded disabled:bg-gray-300 disabled:text-gray-500"
              >
                Merge
              </button>
              <button
                onClick={() => {
                  setShowMergeMode(false)
                  setSelectedThreads(new Set())
                }}
                className="px-3 py-1 bg-gray-300 text-gray-700 text-sm rounded hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Stats */}
        <div className="mt-3 text-xs text-gray-500 flex items-center gap-4">
          <span>{hierarchy.totalThreads} threads</span>
          <span>Max depth: {hierarchy.maxDepth}</span>
        </div>
      </div>

      {/* Thread list */}
      <div className="flex-1 overflow-auto">
        {filteredRootThreads.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            {searchQuery ? 'No threads match your search' : 'No threads yet'}
          </div>
        ) : (
          <div className="p-2">
            {filteredRootThreads.map(rootNode => (
              <ThreadNodeComponent
                key={rootNode.thread.id}
                node={rootNode}
                depth={0}
                isExpanded={expandedThreads.has(rootNode.thread.id)}
                isActive={activeThreadId === rootNode.thread.id}
                isSelected={selectedThreads.has(rootNode.thread.id)}
                showMergeMode={showMergeMode}
                onToggleExpanded={toggleExpanded}
                onSelect={handleThreadSelect}
                onBranch={onThreadCreate}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// Individual thread node component
interface ThreadNodeProps {
  node: ThreadNode
  depth: number
  isExpanded: boolean
  isActive: boolean
  isSelected: boolean
  showMergeMode: boolean
  onToggleExpanded: (threadId: string) => void
  onSelect: (threadId: string) => void
  onBranch: (parentThreadId: string) => void
}

const ThreadNodeComponent: React.FC<ThreadNodeProps> = ({
  node,
  depth,
  isExpanded,
  isActive,
  isSelected,
  showMergeMode,
  onToggleExpanded,
  onSelect,
  onBranch,
}) => {
  const { thread, children } = node
  const hasChildren = children.length > 0
  const indentation = depth * 20

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-100'
      case 'resolved': return 'text-blue-600 bg-blue-100'
      case 'archived': return 'text-gray-600 bg-gray-100'
      case 'merged': return 'text-purple-600 bg-purple-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  return (
    <div className="thread-node">
      <div
        className={`flex items-center gap-2 p-2 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors ${
          isActive ? 'bg-blue-100 border border-blue-300' : ''
        } ${isSelected ? 'bg-yellow-100 border border-yellow-300' : ''}`}
        style={{ paddingLeft: `${8 + indentation}px` }}
        onClick={() => onSelect(thread.id)}
      >
        {/* Expand/collapse button */}
        <button
          onClick={(e) => {
            e.stopPropagation()
            onToggleExpanded(thread.id)
          }}
          className="p-1 hover:bg-gray-200 rounded"
          disabled={!hasChildren}
        >
          {hasChildren ? (
            isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />
          ) : (
            <div className="w-3 h-3" />
          )}
        </button>

        {/* Thread info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-medium text-sm text-gray-800 truncate">
              {thread.title}
            </span>
            <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${getStatusColor(thread.status)}`}>
              {thread.status}
            </span>
            {thread.branchCount > 0 && (
              <span className="flex items-center gap-1 text-xs text-gray-500">
                <GitBranch className="w-3 h-3" />
                {thread.branchCount}
              </span>
            )}
          </div>

          <div className="flex items-center gap-3 text-xs text-gray-500">
            <span>{thread.messageCount} messages</span>
            <span>{formatRelativeTime(thread.lastActivity)}</span>
            {thread.topic && (
              <span className="flex items-center gap-1">
                <Tag className="w-3 h-3" />
                {thread.topic}
              </span>
            )}
          </div>

          {/* Tags */}
          {thread.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {thread.tags.slice(0, 3).map(tag => (
                <span key={tag} className="px-1.5 py-0.5 bg-gray-200 text-gray-700 text-xs rounded">
                  {tag}
                </span>
              ))}
              {thread.tags.length > 3 && (
                <span className="text-xs text-gray-500">+{thread.tags.length - 3}</span>
              )}
            </div>
          )}
        </div>

        {/* Actions */}
        {!showMergeMode && (
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={(e) => {
                e.stopPropagation()
                onBranch(thread.id)
              }}
              className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded"
              title="Create branch"
            >
              <GitBranch className="w-3 h-3" />
            </button>
          </div>
        )}
      </div>

      {/* Children */}
      {hasChildren && isExpanded && (
        <div className="ml-2 border-l border-gray-200">
          {children.map(childNode => (
            <ThreadNodeComponent
              key={childNode.thread.id}
              node={childNode}
              depth={depth + 1}
              isExpanded={expandedThreads.has(childNode.thread.id)}
              isActive={activeThreadId === childNode.thread.id}
              isSelected={selectedThreads.has(childNode.thread.id)}
              showMergeMode={showMergeMode}
              onToggleExpanded={onToggleExpanded}
              onSelect={onSelect}
              onBranch={onBranch}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// Utility functions
function searchInNode(node: ThreadNode, query: string): boolean {
  const thread = node.thread
  const searchableText = [
    thread.title,
    thread.topic || '',
    thread.summary || '',
    ...thread.tags
  ].join(' ').toLowerCase()

  if (searchableText.includes(query)) {
    return true
  }

  return node.children.some(child => searchInNode(child, query))
}

function formatRelativeTime(date: Date): string {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor(diff / (1000 * 60))

  if (days > 0) return `${days}d ago`
  if (hours > 0) return `${hours}h ago`
  if (minutes > 0) return `${minutes}m ago`
  return 'just now'
}
```

## 🎯 **Usage Examples**

### **Basic Threading Integration**
```typescript
// In your chat container
const ConversationWithThreading: React.FC = () => {
  const [threads, setThreads] = useState<ThreadHierarchy | null>(null)
  const [activeThreadId, setActiveThreadId] = useState<string>()
  
  useEffect(() => {
    // Load thread hierarchy
    const hierarchy = conversationThreading.getThreadHierarchy(conversationId)
    setThreads(hierarchy)
  }, [conversationId])

  const handleNewMessage = async (content: string, topics: string[]) => {
    // Add message with automatic thread detection
    if (activeThreadId) {
      const result = await conversationThreading.addMessageToThread(
        messageId,
        activeThreadId,
        { topics, autoCreateBranch: true }
      )

      if (result.branched) {
        // Switch to new branch
        setActiveThreadId(result.branched.id)
      }
    }
  }

  return (
    <div className="conversation-with-threading flex h-screen">
      <ConversationThreadView
        hierarchy={threads}
        activeThreadId={activeThreadId}
        onThreadSelect={setActiveThreadId}
        onThreadCreate={(parentId) => createNewThread(parentId)}
        onThreadMerge={(source, target) => mergeThreads(source, target)}
        className="w-80"
      />
      
      <div className="flex-1">
        {/* Main chat interface filtered by active thread */}
        <ThreadedChatInterface threadId={activeThreadId} />
      </div>
    </div>
  )
}
```

## 🎯 **Key Takeaways**

1. **Visual hierarchy helps navigation** - Tree views make complex threads understandable
2. **Automatic branching reduces cognitive load** - Let AI suggest when to branch
3. **Topic detection improves organization** - Auto-classify message topics
4. **Search across threads is essential** - Find messages in specific discussion branches
5. **Merge capability prevents fragmentation** - Allow users to combine related threads
6. **Depth limits prevent complexity** - Cap thread nesting to maintain usability
7. **Status tracking aids organization** - Mark threads as resolved, archived, etc.

---

**Next**: [06-advanced-search-and-filtering.md](./06-advanced-search-and-filtering.md) - Powerful Search Features

**Previous**: [04-message-persistence-system.md](./04-message-persistence-system.md)