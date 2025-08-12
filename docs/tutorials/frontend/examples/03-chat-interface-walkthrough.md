# Examples 3: Chat Interface Walkthrough - Complete Chat Implementation

## 🎯 **Learning Objectives**

By the end of this walkthrough, you will understand:
- Complete implementation of a production-ready chat interface
- Integration of all streaming, error handling, and persistence features
- Real-world code organization and component composition patterns
- Advanced UX patterns for chat applications
- Performance optimization techniques in practice
- Testing approaches for complex chat components

## 🚀 **The Complete Chat Interface**

This walkthrough demonstrates how all the concepts from previous tutorials combine into a production-ready chat interface. We'll build the main `ChatContainer` component that powers the Agent Network Sandbox.

## 🏗️ **Architecture Overview**

Our chat interface consists of these key components:

```
ChatContainer
├── ChatHeader (conversation info, actions)
├── MessageList (virtualized message display)
│   ├── MessageItem (individual message rendering)
│   └── StreamingMessage (real-time message streaming)
├── MessageInput (user input with advanced features)
├── SidePanel (search, threading, export)
└── StatusBar (connection status, typing indicators)
```

### **Step 1: Main Chat Container**

```typescript
// src/components/ChatContainer.tsx
import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  MessageSquare, 
  Search, 
  Settings, 
  Download, 
  AlertTriangle,
  Wifi,
  WifiOff
} from 'lucide-react'

// Hooks
import { useStreamingOrchestrator } from '../hooks/useStreamingOrchestrator'
import { useMessagePersistence } from '../hooks/useMessagePersistence'
import { useConversationState } from '../hooks/useConversationState'
import { useErrorReporting } from '../hooks/useErrorReporting'
import { usePerformanceMonitoring } from '../hooks/usePerformanceMonitoring'

// Components
import { ChatHeader } from './ChatHeader'
import { MessageList } from './MessageList'
import { MessageInput } from './MessageInput'
import { SidePanel } from './SidePanel'
import { StatusBar } from './StatusBar'
import { StreamingErrorBoundary } from './StreamingErrorBoundary'
import { LoadingSpinner } from './ui/LoadingSpinner'
import { ErrorDisplay } from './ui/ErrorDisplay'

// Types
import { StoredMessage, ProcessResponse } from '../types'
import { environmentManager } from '../config/environment'

interface ChatContainerProps {
  className?: string
  showSidebar?: boolean
  enableThreading?: boolean
  enableSearch?: boolean
  enableExport?: boolean
}

export const ChatContainer: React.FC<ChatContainerProps> = ({
  className = '',
  showSidebar = true,
  enableThreading = environmentManager.isFeatureEnabled('enableConversationThreading'),
  enableSearch = environmentManager.isFeatureEnabled('enableAdvancedSearch'),
  enableExport = environmentManager.isFeatureEnabled('enableMessageExport')
}) => {
  // Router state
  const { conversationId } = useParams<{ conversationId: string }>()
  const navigate = useNavigate()

  // Component state
  const [sidebarOpen, setSidebarOpen] = useState(showSidebar)
  const [activePanel, setActivePanel] = useState<'messages' | 'search' | 'settings'>('messages')
  const [isOnline, setIsOnline] = useState(navigator.onLine)

  // Refs for performance optimization
  const messageListRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const lastMessageRef = useRef<string>()

  // Custom hooks
  const {
    streamMessage,
    isLoading,
    error: streamingError,
    response,
    getCurrentContent,
    isCurrentlyStreaming
  } = useStreamingOrchestrator()

  const {
    messages,
    isLoading: messagesLoading,
    error: messagesError,
    addMessage,
    updateMessage,
    deleteMessage,
    searchMessages
  } = useConversationState(conversationId || 'default')

  const {
    saveMessage,
    loadMessages,
    exportMessages,
    getConversationStats
  } = useMessagePersistence()

  const { reportAsyncError, reportUserAction } = useErrorReporting()
  const { recordRenderTime } = usePerformanceMonitoring('ChatContainer')

  // Derived state
  const hasMessages = messages.length > 0
  const canSendMessage = !isLoading && !isCurrentlyStreaming()
  const currentError = streamingError || messagesError

  // Network status monitoring
  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  // Auto-scroll to bottom for new messages
  useEffect(() => {
    if (messages.length > 0 && messageListRef.current) {
      const lastMessage = messages[messages.length - 1]
      if (lastMessage.id !== lastMessageRef.current) {
        lastMessageRef.current = lastMessage.id
        
        // Smooth scroll to bottom
        messageListRef.current.scrollTo({
          top: messageListRef.current.scrollHeight,
          behavior: 'smooth'
        })
      }
    }
  }, [messages])

  // Performance monitoring
  useEffect(() => {
    recordRenderTime()
  })

  // Message sending handler
  const handleSendMessage = useCallback(async (content: string) => {
    if (!content.trim() || !canSendMessage) return

    const messageId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    const conversationIdActual = conversationId || 'default'

    try {
      // Create user message
      const userMessage: StoredMessage = {
        id: messageId,
        content: content.trim(),
        role: 'user',
        timestamp: new Date(),
        conversationId: conversationIdActual,
      }

      // Add to UI immediately (optimistic update)
      await addMessage(userMessage)

      // Save to persistence layer
      await saveMessage(userMessage)

      // Report user action
      reportUserAction('send_message', {
        messageLength: content.length,
        conversationId: conversationIdActual,
        hasHistory: hasMessages
      })

      // Stream AI response
      await streamMessage(content, {
        onData: (chunk) => {
          // Real-time chunk updates handled by StreamingMessage component
        },
        onComplete: async (finalResponse: ProcessResponse) => {
          try {
            // Create assistant message
            const assistantMessage: StoredMessage = {
              id: finalResponse.id,
              content: finalResponse.content,
              role: 'assistant',
              timestamp: finalResponse.timestamp,
              conversationId: conversationIdActual,
              metadata: {
                agentId: finalResponse.agentId,
                processingTime: finalResponse.processingTime,
                tokens: finalResponse.tokens,
              }
            }

            // Add to UI
            await addMessage(assistantMessage)

            // Save to persistence
            await saveMessage(assistantMessage)

            // Focus back to input
            inputRef.current?.focus()

          } catch (persistError) {
            reportAsyncError(persistError as Error, {
              context: 'message_persistence',
              messageId: finalResponse.id
            })
          }
        },
        onError: (error) => {
          reportAsyncError(error, {
            context: 'streaming_response',
            userMessage: content,
            conversationId: conversationIdActual
          })
        }
      })

    } catch (error) {
      // Remove optimistic update on error
      await deleteMessage(messageId)
      
      reportAsyncError(error as Error, {
        context: 'send_message',
        messageContent: content,
        conversationId: conversationIdActual
      })
    }
  }, [
    conversationId,
    canSendMessage,
    hasMessages,
    addMessage,
    saveMessage,
    streamMessage,
    deleteMessage,
    reportAsyncError,
    reportUserAction
  ])

  // Message retry handler
  const handleRetryMessage = useCallback(async (messageId: string) => {
    try {
      const message = messages.find(m => m.id === messageId)
      if (!message) return

      // Find the previous user message
      const messageIndex = messages.findIndex(m => m.id === messageId)
      const userMessage = messages
        .slice(0, messageIndex)
        .reverse()
        .find(m => m.role === 'user')

      if (userMessage) {
        // Remove the failed message
        await deleteMessage(messageId)
        
        // Retry with the original user message
        await handleSendMessage(userMessage.content)
      }
    } catch (error) {
      reportAsyncError(error as Error, {
        context: 'message_retry',
        messageId
      })
    }
  }, [messages, deleteMessage, handleSendMessage, reportAsyncError])

  // Message editing handler
  const handleEditMessage = useCallback(async (messageId: string, newContent: string) => {
    try {
      const message = messages.find(m => m.id === messageId)
      if (!message) return

      const updatedMessage = {
        ...message,
        content: newContent,
        editedAt: new Date()
      }

      await updateMessage(messageId, updatedMessage)
      await saveMessage(updatedMessage)

      reportUserAction('edit_message', {
        messageId,
        originalLength: message.content.length,
        newLength: newContent.length
      })

    } catch (error) {
      reportAsyncError(error as Error, {
        context: 'message_edit',
        messageId
      })
    }
  }, [messages, updateMessage, saveMessage, reportUserAction, reportAsyncError])

  // Export conversation handler
  const handleExportConversation = useCallback(async (format: 'json' | 'csv' | 'txt') => {
    try {
      reportUserAction('export_conversation', {
        format,
        messageCount: messages.length,
        conversationId
      })

      const blob = await exportMessages(conversationId || 'default', format)
      
      // Create download link
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `conversation-${conversationId}-${format}.${format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

    } catch (error) {
      reportAsyncError(error as Error, {
        context: 'export_conversation',
        format,
        conversationId
      })
    }
  }, [messages.length, conversationId, exportMessages, reportUserAction, reportAsyncError])

  // Search handler
  const handleSearch = useCallback(async (query: string) => {
    try {
      reportUserAction('search_messages', {
        query: query.length, // Don't log actual query for privacy
        conversationId
      })

      const results = await searchMessages(query)
      setActivePanel('search')
      
      return results
    } catch (error) {
      reportAsyncError(error as Error, {
        context: 'message_search',
        conversationId
      })
      return []
    }
  }, [conversationId, searchMessages, reportUserAction, reportAsyncError])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + K for search
      if ((e.metaKey || e.ctrlKey) && e.key === 'k' && enableSearch) {
        e.preventDefault()
        setActivePanel('search')
        setSidebarOpen(true)
      }

      // Cmd/Ctrl + E for export
      if ((e.metaKey || e.ctrlKey) && e.key === 'e' && enableExport) {
        e.preventDefault()
        handleExportConversation('json')
      }

      // Escape to close sidebar
      if (e.key === 'Escape' && sidebarOpen) {
        setSidebarOpen(false)
        inputRef.current?.focus()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [enableSearch, enableExport, sidebarOpen, handleExportConversation])

  // Loading state
  if (messagesLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="large" />
        <span className="ml-3 text-gray-600">Loading conversation...</span>
      </div>
    )
  }

  // Error state
  if (currentError) {
    return (
      <ErrorDisplay
        error={currentError}
        onRetry={() => window.location.reload()}
        title="Chat Error"
        description="Failed to load the chat interface. Please try again."
      />
    )
  }

  return (
    <div className={`chat-container flex h-full bg-white ${className}`}>
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <ChatHeader
          conversationId={conversationId}
          messageCount={messages.length}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          onExport={enableExport ? handleExportConversation : undefined}
          onSettings={() => setActivePanel('settings')}
        />

        {/* Messages */}
        <div className="flex-1 overflow-hidden">
          <StreamingErrorBoundary
            onStreamingError={(error) => {
              reportAsyncError(error, { context: 'streaming_error_boundary' })
            }}
          >
            <MessageList
              ref={messageListRef}
              messages={messages}
              currentStreamingContent={getCurrentContent()}
              isStreaming={isCurrentlyStreaming()}
              onRetryMessage={handleRetryMessage}
              onEditMessage={handleEditMessage}
              onDeleteMessage={deleteMessage}
              className="h-full"
            />
          </StreamingErrorBoundary>
        </div>

        {/* Input */}
        <div className="border-t border-gray-200 p-4">
          <MessageInput
            ref={inputRef}
            onSendMessage={handleSendMessage}
            disabled={!canSendMessage}
            placeholder={
              !isOnline 
                ? "You're offline. Connect to send messages."
                : isLoading 
                ? "Processing message..."
                : "Type a message..."
            }
            showSendButton={true}
            enableMarkdown={true}
            enableAttachments={false}
            maxLength={4000}
          />
        </div>

        {/* Status Bar */}
        <StatusBar
          isOnline={isOnline}
          isProcessing={isLoading}
          connectionStatus={isOnline ? 'connected' : 'disconnected'}
          messageCount={messages.length}
          conversationStats={getConversationStats(conversationId || 'default')}
        />
      </div>

      {/* Sidebar */}
      {showSidebar && (
        <div className={`sidebar-container transition-transform duration-300 ${
          sidebarOpen ? 'translate-x-0' : 'translate-x-full'
        }`}>
          <SidePanel
            activePanel={activePanel}
            onPanelChange={setActivePanel}
            onSearch={enableSearch ? handleSearch : undefined}
            onExport={enableExport ? handleExportConversation : undefined}
            messages={messages}
            conversationId={conversationId}
            enableThreading={enableThreading}
            onClose={() => setSidebarOpen(false)}
            className="w-80 border-l border-gray-200"
          />
        </div>
      )}
    </div>
  )
}

export default ChatContainer
```

### **Step 2: Chat Header Component**

```typescript
// src/components/ChatHeader.tsx
import React, { useState, useMemo } from 'react'
import { 
  MessageSquare, 
  Settings, 
  Download, 
  Sidebar, 
  MoreVertical,
  Info,
  Share,
  Archive
} from 'lucide-react'
import { Button } from './ui/Button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from './ui/DropdownMenu'

interface ChatHeaderProps {
  conversationId?: string
  messageCount: number
  onToggleSidebar: () => void
  onExport?: (format: 'json' | 'csv' | 'txt') => void
  onSettings: () => void
  className?: string
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  conversationId = 'default',
  messageCount,
  onToggleSidebar,
  onExport,
  onSettings,
  className = ''
}) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)

  // Generate conversation title based on ID and message count
  const conversationTitle = useMemo(() => {
    if (conversationId === 'default') {
      return messageCount > 0 ? 'Chat Conversation' : 'New Conversation'
    }
    
    // Format conversation ID for display
    const parts = conversationId.split('-')
    if (parts.length > 2) {
      return `Conversation ${parts[parts.length - 1].toUpperCase()}`
    }
    
    return `Conversation ${conversationId.slice(-8).toUpperCase()}`
  }, [conversationId, messageCount])

  const conversationSubtitle = useMemo(() => {
    if (messageCount === 0) return 'Start a conversation'
    if (messageCount === 1) return '1 message'
    return `${messageCount} messages`
  }, [messageCount])

  return (
    <header className={`chat-header bg-white border-b border-gray-200 px-4 py-3 ${className}`}>
      <div className="flex items-center justify-between">
        {/* Left side - Conversation info */}
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 bg-blue-100 rounded-lg">
            <MessageSquare className="w-5 h-5 text-blue-600" />
          </div>
          
          <div>
            <h1 className="text-lg font-semibold text-gray-900 line-clamp-1">
              {conversationTitle}
            </h1>
            <p className="text-sm text-gray-500">
              {conversationSubtitle}
            </p>
          </div>
        </div>

        {/* Right side - Actions */}
        <div className="flex items-center gap-2">
          {/* Toggle Sidebar */}
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleSidebar}
            aria-label="Toggle sidebar"
          >
            <Sidebar className="w-4 h-4" />
          </Button>

          {/* More Actions Dropdown */}
          <DropdownMenu open={isDropdownOpen} onOpenChange={setIsDropdownOpen}>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                aria-label="More actions"
              >
                <MoreVertical className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            
            <DropdownMenuContent align="end" className="w-48">
              {/* Conversation Info */}
              <DropdownMenuItem onClick={() => console.log('Show conversation info')}>
                <Info className="w-4 h-4 mr-2" />
                Conversation Info
              </DropdownMenuItem>

              {/* Export Options */}
              {onExport && messageCount > 0 && (
                <>
                  <DropdownMenuItem onClick={() => onExport('json')}>
                    <Download className="w-4 h-4 mr-2" />
                    Export as JSON
                  </DropdownMenuItem>
                  
                  <DropdownMenuItem onClick={() => onExport('csv')}>
                    <Download className="w-4 h-4 mr-2" />
                    Export as CSV
                  </DropdownMenuItem>
                  
                  <DropdownMenuItem onClick={() => onExport('txt')}>
                    <Download className="w-4 h-4 mr-2" />
                    Export as Text
                  </DropdownMenuItem>
                </>
              )}

              {/* Share */}
              <DropdownMenuItem 
                onClick={() => {
                  if (navigator.share) {
                    navigator.share({
                      title: conversationTitle,
                      text: `Chat conversation with ${messageCount} messages`,
                      url: window.location.href
                    })
                  } else {
                    navigator.clipboard.writeText(window.location.href)
                  }
                }}
              >
                <Share className="w-4 h-4 mr-2" />
                Share Conversation
              </DropdownMenuItem>

              {/* Archive */}
              {messageCount > 0 && (
                <DropdownMenuItem onClick={() => console.log('Archive conversation')}>
                  <Archive className="w-4 h-4 mr-2" />
                  Archive
                </DropdownMenuItem>
              )}

              {/* Settings */}
              <DropdownMenuItem onClick={onSettings}>
                <Settings className="w-4 h-4 mr-2" />
                Settings
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Progress indicator for active streaming */}
      <div className="mt-2 h-1 bg-gray-100 rounded-full overflow-hidden">
        <div 
          className="h-full bg-blue-500 transition-all duration-300"
          style={{ width: messageCount > 0 ? '100%' : '0%' }}
        />
      </div>
    </header>
  )
}
```

### **Step 3: Status Bar Component**

```typescript
// src/components/StatusBar.tsx
import React, { useMemo } from 'react'
import { Wifi, WifiOff, Clock, MessageSquare, Zap, AlertCircle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface ConversationStats {
  totalMessages: number
  totalTokens?: number
  averageResponseTime?: number
  lastActivity?: Date
  conversationDuration?: number
}

interface StatusBarProps {
  isOnline: boolean
  isProcessing: boolean
  connectionStatus: 'connected' | 'connecting' | 'disconnected' | 'reconnecting'
  messageCount: number
  conversationStats?: ConversationStats
  className?: string
}

export const StatusBar: React.FC<StatusBarProps> = ({
  isOnline,
  isProcessing,
  connectionStatus,
  messageCount,
  conversationStats,
  className = ''
}) => {
  // Connection status display
  const connectionDisplay = useMemo(() => {
    switch (connectionStatus) {
      case 'connected':
        return {
          icon: <Wifi className="w-3 h-3 text-green-500" />,
          text: 'Connected',
          className: 'text-green-600'
        }
      case 'connecting':
        return {
          icon: <Wifi className="w-3 h-3 text-yellow-500 animate-pulse" />,
          text: 'Connecting...',
          className: 'text-yellow-600'
        }
      case 'reconnecting':
        return {
          icon: <Wifi className="w-3 h-3 text-yellow-500 animate-pulse" />,
          text: 'Reconnecting...',
          className: 'text-yellow-600'
        }
      case 'disconnected':
        return {
          icon: <WifiOff className="w-3 h-3 text-red-500" />,
          text: 'Disconnected',
          className: 'text-red-600'
        }
      default:
        return {
          icon: <AlertCircle className="w-3 h-3 text-gray-500" />,
          text: 'Unknown',
          className: 'text-gray-600'
        }
    }
  }, [connectionStatus])

  // Format last activity time
  const lastActivityDisplay = useMemo(() => {
    if (!conversationStats?.lastActivity) return null
    
    try {
      return formatDistanceToNow(conversationStats.lastActivity, { addSuffix: true })
    } catch {
      return null
    }
  }, [conversationStats?.lastActivity])

  // Format average response time
  const avgResponseTimeDisplay = useMemo(() => {
    if (!conversationStats?.averageResponseTime) return null
    
    const time = conversationStats.averageResponseTime
    if (time < 1000) {
      return `${Math.round(time)}ms`
    } else {
      return `${(time / 1000).toFixed(1)}s`
    }
  }, [conversationStats?.averageResponseTime])

  return (
    <div className={`status-bar bg-gray-50 border-t border-gray-200 px-4 py-2 ${className}`}>
      <div className="flex items-center justify-between text-xs text-gray-600">
        {/* Left side - Connection status */}
        <div className="flex items-center gap-4">
          <div className={`flex items-center gap-1 ${connectionDisplay.className}`}>
            {connectionDisplay.icon}
            <span>{connectionDisplay.text}</span>
          </div>

          {isProcessing && (
            <div className="flex items-center gap-1 text-blue-600">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
              <span>Processing...</span>
            </div>
          )}
        </div>

        {/* Right side - Conversation stats */}
        <div className="flex items-center gap-4">
          {/* Message count */}
          <div className="flex items-center gap-1">
            <MessageSquare className="w-3 h-3" />
            <span>{messageCount} messages</span>
          </div>

          {/* Token count */}
          {conversationStats?.totalTokens && (
            <div className="flex items-center gap-1">
              <Zap className="w-3 h-3" />
              <span>{conversationStats.totalTokens.toLocaleString()} tokens</span>
            </div>
          )}

          {/* Average response time */}
          {avgResponseTimeDisplay && (
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              <span>~{avgResponseTimeDisplay}</span>
            </div>
          )}

          {/* Last activity */}
          {lastActivityDisplay && (
            <div className="flex items-center gap-1">
              <span>Active {lastActivityDisplay}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
```

### **Step 4: Advanced Message Input Component**

```typescript
// src/components/MessageInput.tsx
import React, { useState, useRef, useCallback, useEffect, forwardRef } from 'react'
import { Send, Paperclip, Mic, Square, Loader2 } from 'lucide-react'
import { Button } from './ui/Button'

interface MessageInputProps {
  onSendMessage: (content: string) => void
  disabled?: boolean
  placeholder?: string
  showSendButton?: boolean
  enableMarkdown?: boolean
  enableAttachments?: boolean
  enableVoiceInput?: boolean
  maxLength?: number
  className?: string
}

export const MessageInput = forwardRef<HTMLTextAreaElement, MessageInputProps>(({
  onSendMessage,
  disabled = false,
  placeholder = "Type a message...",
  showSendButton = true,
  enableMarkdown = false,
  enableAttachments = false,
  enableVoiceInput = false,
  maxLength = 4000,
  className = ''
}, ref) => {
  const [message, setMessage] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [isComposing, setIsComposing] = useState(false)
  
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Combine refs
  const combinedRef = useCallback((node: HTMLTextAreaElement) => {
    textareaRef.current = node
    if (ref) {
      if (typeof ref === 'function') {
        ref(node)
      } else {
        ref.current = node
      }
    }
  }, [ref])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`
    }
  }, [message])

  // Send message handler
  const handleSend = useCallback(() => {
    const trimmedMessage = message.trim()
    if (!trimmedMessage || disabled) return

    onSendMessage(trimmedMessage)
    setMessage('')
    textareaRef.current?.focus()
  }, [message, disabled, onSendMessage])

  // Keyboard handler
  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter') {
      if (e.shiftKey) {
        // Shift+Enter for new line
        return
      } else {
        // Enter to send (if not composing)
        e.preventDefault()
        if (!isComposing) {
          handleSend()
        }
      }
    }
  }, [handleSend, isComposing])

  // Input composition handlers (for IME support)
  const handleCompositionStart = useCallback(() => {
    setIsComposing(true)
  }, [])

  const handleCompositionEnd = useCallback(() => {
    setIsComposing(false)
  }, [])

  // File attachment handler
  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    // Handle file upload (implementation depends on your backend)
    console.log('Files selected:', Array.from(files))
    
    // Reset file input
    e.target.value = ''
  }, [])

  // Voice recording handlers
  const handleStartRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      setIsRecording(true)
      
      // Start recording logic here
      console.log('Recording started', stream)
    } catch (error) {
      console.error('Failed to start recording:', error)
    }
  }, [])

  const handleStopRecording = useCallback(() => {
    setIsRecording(false)
    // Stop recording logic here
    console.log('Recording stopped')
  }, [])

  const canSend = message.trim().length > 0 && !disabled
  const characterCount = message.length
  const isNearLimit = characterCount > maxLength * 0.9
  const isOverLimit = characterCount > maxLength

  return (
    <div className={`message-input bg-white border border-gray-300 rounded-lg p-3 ${className}`}>
      <div className="flex items-end gap-2">
        {/* Attachment button */}
        {enableAttachments && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
            aria-label="Attach file"
            className="flex-shrink-0"
          >
            <Paperclip className="w-4 h-4" />
          </Button>
        )}

        {/* Text input */}
        <div className="flex-1 relative">
          <textarea
            ref={combinedRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            onCompositionStart={handleCompositionStart}
            onCompositionEnd={handleCompositionEnd}
            placeholder={placeholder}
            disabled={disabled}
            maxLength={maxLength}
            rows={1}
            className="w-full resize-none border-0 outline-none placeholder-gray-500 bg-transparent"
            style={{ minHeight: '24px', maxHeight: '120px' }}
            aria-label="Message input"
          />
          
          {/* Character count indicator */}
          {(isNearLimit || isOverLimit) && (
            <div className={`absolute bottom-1 right-1 text-xs ${
              isOverLimit ? 'text-red-500' : 'text-yellow-500'
            }`}>
              {characterCount}/{maxLength}
            </div>
          )}
        </div>

        {/* Voice input button */}
        {enableVoiceInput && (
          <Button
            type="button"
            variant={isRecording ? "destructive" : "ghost"}
            size="sm"
            onClick={isRecording ? handleStopRecording : handleStartRecording}
            disabled={disabled}
            aria-label={isRecording ? "Stop recording" : "Start voice recording"}
            className="flex-shrink-0"
          >
            {isRecording ? (
              <Square className="w-4 h-4" />
            ) : (
              <Mic className="w-4 h-4" />
            )}
          </Button>
        )}

        {/* Send button */}
        {showSendButton && (
          <Button
            type="button"
            onClick={handleSend}
            disabled={!canSend || isOverLimit}
            size="sm"
            className="flex-shrink-0"
            aria-label="Send message"
          >
            {disabled ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        )}
      </div>

      {/* Hidden file input */}
      {enableAttachments && (
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          accept="image/*,text/*,.pdf,.doc,.docx"
        />
      )}

      {/* Markdown hint */}
      {enableMarkdown && message.length > 0 && (
        <div className="mt-2 text-xs text-gray-500">
          **bold**, *italic*, `code`, > quote supported
        </div>
      )}
    </div>
  )
})

MessageInput.displayName = 'MessageInput'
```

## 🎯 **Key Integration Patterns**

### **1. State Management Integration**
```typescript
// Combining multiple hooks for comprehensive state management
const {
  // Streaming functionality
  streamMessage, isLoading, error: streamingError
} = useStreamingOrchestrator()

const {
  // Message persistence
  messages, addMessage, updateMessage, deleteMessage
} = useConversationState(conversationId)

const {
  // Error reporting and analytics
  reportAsyncError, reportUserAction
} = useErrorReporting()
```

### **2. Error Boundary Integration**
```typescript
// Wrapping streaming components in error boundaries
<StreamingErrorBoundary
  onStreamingError={(error) => {
    reportAsyncError(error, { context: 'streaming_error_boundary' })
  }}
>
  <MessageList {...props} />
</StreamingErrorBoundary>
```

### **3. Performance Optimization**
```typescript
// Memoized callbacks to prevent unnecessary re-renders
const handleSendMessage = useCallback(async (content: string) => {
  // Implementation
}, [/* dependencies */])

// Performance monitoring integration
const { recordRenderTime } = usePerformanceMonitoring('ChatContainer')
useEffect(() => { recordRenderTime() })
```

### **4. Accessibility Features**
```typescript
// Comprehensive ARIA labels and keyboard navigation
<Button
  variant="ghost"
  size="sm"
  onClick={onToggleSidebar}
  aria-label="Toggle sidebar"
>
  <Sidebar className="w-4 h-4" />
</Button>

// Screen reader announcements
<div aria-live="polite" aria-atomic="true" className="sr-only">
  {isLoading && "Processing message..."}
  {error && "An error occurred"}
</div>
```

## 🎯 **Key Takeaways**

1. **Component composition over inheritance** - Build complex UIs from simple, focused components
2. **Comprehensive error handling** - Multiple error boundaries and fallback strategies
3. **Performance-first architecture** - Memoization, virtualization, and optimistic updates
4. **Accessibility by design** - ARIA labels, keyboard navigation, and screen reader support
5. **Real-time user feedback** - Loading states, progress indicators, and status information
6. **Modular and testable** - Each component has a single responsibility and clear interfaces
7. **Production-ready patterns** - Monitoring, error reporting, and feature flags integration

---

**Next**: [04-streaming-implementation-deep-dive.md](./04-streaming-implementation-deep-dive.md) - Advanced Streaming Patterns

**Previous**: [02-message-persistence-walkthrough.md](./02-message-persistence-walkthrough.md)