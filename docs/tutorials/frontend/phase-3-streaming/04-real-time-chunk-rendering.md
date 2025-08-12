# Phase 3.4: Real-time Chunk Rendering - Streaming Message Display

## 🎯 **Learning Objectives**

By the end of this tutorial, you will:
- Build real-time message rendering that displays chunks as they arrive
- Implement smooth streaming animations and visual feedback
- Handle partial content display and progressive enhancement
- Create responsive streaming interfaces that work on all devices
- Optimize rendering performance for high-frequency chunk updates

## 🚀 **The Real-time Rendering Challenge**

Streaming responses arrive chunk-by-chunk, creating unique UX challenges:
- **Partial content display**: Show incomplete sentences gracefully
- **Visual continuity**: Smooth transitions between chunks
- **Performance**: Handle rapid chunk updates without blocking UI
- **User feedback**: Clear indication that content is still loading
- **Error handling**: Graceful fallback when streaming fails

**Our goal**: Create a **smooth, responsive streaming experience** that feels natural and informative.

## 🎨 **Streaming Message Component Architecture**

### **Step 1: Streaming Message State Management**

```typescript
// src/components/StreamingMessage.tsx
import React, { useState, useEffect, useRef, useMemo } from 'react'
import { marked } from 'marked'

export interface StreamingChunk {
  id: string
  content: string
  timestamp: Date
  isComplete: boolean
}

export interface StreamingMessageProps {
  chunks: StreamingChunk[]
  isStreaming: boolean
  agentName: string
  protocol: string
  onComplete?: (finalContent: string) => void
  className?: string
}

interface StreamingState {
  displayedContent: string
  isTyping: boolean
  lastChunkTime: Date | null
  chunkCount: number
  estimatedWordsPerSecond: number
}

export const StreamingMessage: React.FC<StreamingMessageProps> = ({
  chunks,
  isStreaming,
  agentName,
  protocol,
  onComplete,
  className = '',
}) => {
  const [streamingState, setStreamingState] = useState<StreamingState>({
    displayedContent: '',
    isTyping: false,
    lastChunkTime: null,
    chunkCount: 0,
    estimatedWordsPerSecond: 0,
  })

  const contentRef = useRef<HTMLDivElement>(null)
  const animationFrameRef = useRef<number>()
  const typingTimeoutRef = useRef<number>()

  // Combine all chunks into final content
  const combinedContent = useMemo(() => {
    return chunks.map(chunk => chunk.content).join('')
  }, [chunks])

  // Process new chunks with smooth transitions
  useEffect(() => {
    if (chunks.length === 0) return

    const latestChunk = chunks[chunks.length - 1]
    const now = new Date()

    // Calculate streaming speed for better UX feedback
    const timeSinceLastChunk = streamingState.lastChunkTime 
      ? now.getTime() - streamingState.lastChunkTime.getTime()
      : 0

    const wordsInChunk = latestChunk.content.split(/\s+/).length
    const wordsPerSecond = timeSinceLastChunk > 0 
      ? (wordsInChunk / timeSinceLastChunk) * 1000
      : streamingState.estimatedWordsPerSecond

    // Update streaming state
    setStreamingState(prev => ({
      displayedContent: combinedContent,
      isTyping: isStreaming,
      lastChunkTime: now,
      chunkCount: chunks.length,
      estimatedWordsPerSecond: wordsPerSecond > 0 ? wordsPerSecond : prev.estimatedWordsPerSecond,
    }))

    // Auto-scroll to bottom as content grows
    if (contentRef.current) {
      smoothScrollToBottom(contentRef.current)
    }

    // Clear typing indicator after delay
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current)
    }
    
    if (isStreaming) {
      typingTimeoutRef.current = window.setTimeout(() => {
        setStreamingState(prev => ({ ...prev, isTyping: false }))
      }, 2000) // Show typing for 2 seconds after last chunk
    }

  }, [chunks, combinedContent, isStreaming, streamingState.lastChunkTime, streamingState.estimatedWordsPerSecond])

  // Handle streaming completion
  useEffect(() => {
    if (!isStreaming && chunks.length > 0) {
      const finalContent = combinedContent
      onComplete?.(finalContent)
      
      setStreamingState(prev => ({
        ...prev,
        isTyping: false,
      }))
    }
  }, [isStreaming, chunks.length, combinedContent, onComplete])

  // Cleanup timers
  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current)
      }
    }
  }, [])

  return (
    <div className={`streaming-message ${className}`}>
      <StreamingHeader 
        agentName={agentName}
        protocol={protocol}
        isStreaming={isStreaming}
        chunkCount={streamingState.chunkCount}
        wordsPerSecond={streamingState.estimatedWordsPerSecond}
      />
      
      <div 
        ref={contentRef}
        className="streaming-content relative overflow-hidden"
      >
        <StreamingContent 
          content={streamingState.displayedContent}
          isStreaming={isStreaming}
          isTyping={streamingState.isTyping}
        />
        
        {streamingState.isTyping && (
          <TypingIndicator className="mt-2" />
        )}
      </div>
      
      <StreamingFooter 
        isComplete={!isStreaming}
        totalChunks={chunks.length}
        streamDuration={calculateStreamDuration(chunks)}
      />
    </div>
  )
}

// Smooth scroll helper
function smoothScrollToBottom(element: HTMLElement) {
  const scrollHeight = element.scrollHeight
  const currentScroll = element.scrollTop + element.clientHeight
  
  // Only scroll if we're near the bottom (within 100px)
  if (scrollHeight - currentScroll <= 100) {
    element.scrollTo({
      top: scrollHeight,
      behavior: 'smooth'
    })
  }
}

// Calculate total streaming duration
function calculateStreamDuration(chunks: StreamingChunk[]): number {
  if (chunks.length < 2) return 0
  
  const firstChunk = chunks[0]
  const lastChunk = chunks[chunks.length - 1]
  
  return lastChunk.timestamp.getTime() - firstChunk.timestamp.getTime()
}
```

### **Step 2: Streaming Content Renderer**

```typescript
// src/components/StreamingContent.tsx
import React, { useMemo } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface StreamingContentProps {
  content: string
  isStreaming: boolean
  isTyping: boolean
}

export const StreamingContent: React.FC<StreamingContentProps> = ({
  content,
  isStreaming,
  isTyping,
}) => {
  // Parse content for different types (markdown, code blocks, etc.)
  const parsedContent = useMemo(() => {
    return parseStreamingContent(content, isStreaming)
  }, [content, isStreaming])

  return (
    <div className="streaming-content-container">
      {parsedContent.blocks.map((block, index) => (
        <ContentBlock
          key={`${block.type}-${index}`}
          block={block}
          isLast={index === parsedContent.blocks.length - 1}
          isStreaming={isStreaming && index === parsedContent.blocks.length - 1}
          isTyping={isTyping && index === parsedContent.blocks.length - 1}
        />
      ))}
    </div>
  )
}

interface ContentBlock {
  type: 'text' | 'code' | 'list' | 'quote' | 'heading'
  content: string
  language?: string
  isComplete: boolean
}

interface ParsedContent {
  blocks: ContentBlock[]
  hasIncompleteBlock: boolean
}

function parseStreamingContent(content: string, isStreaming: boolean): ParsedContent {
  const blocks: ContentBlock[] = []
  let hasIncompleteBlock = false

  // Simple parsing for streaming content
  // In a full implementation, you'd use a proper markdown parser
  
  const lines = content.split('\n')
  let currentBlock: ContentBlock | null = null
  let inCodeBlock = false
  let codeLanguage = ''

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    
    // Code block detection
    if (line.startsWith('```')) {
      if (inCodeBlock) {
        // End of code block
        if (currentBlock && currentBlock.type === 'code') {
          currentBlock.isComplete = true
          blocks.push(currentBlock)
          currentBlock = null
        }
        inCodeBlock = false
        codeLanguage = ''
      } else {
        // Start of code block
        codeLanguage = line.substring(3).trim()
        currentBlock = {
          type: 'code',
          content: '',
          language: codeLanguage || 'text',
          isComplete: false,
        }
        inCodeBlock = true
      }
      continue
    }

    if (inCodeBlock) {
      if (currentBlock) {
        currentBlock.content += (currentBlock.content ? '\n' : '') + line
      }
      continue
    }

    // Heading detection
    if (line.startsWith('#')) {
      if (currentBlock) {
        blocks.push(currentBlock)
      }
      currentBlock = {
        type: 'heading',
        content: line,
        isComplete: true,
      }
      blocks.push(currentBlock)
      currentBlock = null
      continue
    }

    // List detection
    if (line.startsWith('- ') || line.startsWith('* ') || /^\d+\./.test(line)) {
      if (currentBlock && currentBlock.type !== 'list') {
        blocks.push(currentBlock)
        currentBlock = null
      }
      
      if (!currentBlock) {
        currentBlock = {
          type: 'list',
          content: line,
          isComplete: false,
        }
      } else {
        currentBlock.content += '\n' + line
      }
      continue
    }

    // Quote detection
    if (line.startsWith('> ')) {
      if (currentBlock && currentBlock.type !== 'quote') {
        blocks.push(currentBlock)
        currentBlock = null
      }
      
      if (!currentBlock) {
        currentBlock = {
          type: 'quote',
          content: line,
          isComplete: false,
        }
      } else {
        currentBlock.content += '\n' + line
      }
      continue
    }

    // Regular text
    if (currentBlock && currentBlock.type !== 'text') {
      blocks.push(currentBlock)
      currentBlock = null
    }
    
    if (!currentBlock) {
      currentBlock = {
        type: 'text',
        content: line,
        isComplete: false,
      }
    } else {
      currentBlock.content += (currentBlock.content && line ? '\n' : '') + line
    }
  }

  // Handle final block
  if (currentBlock) {
    if (isStreaming) {
      hasIncompleteBlock = true
    } else {
      currentBlock.isComplete = true
    }
    blocks.push(currentBlock)
  }

  return { blocks, hasIncompleteBlock }
}

interface ContentBlockProps {
  block: ContentBlock
  isLast: boolean
  isStreaming: boolean
  isTyping: boolean
}

const ContentBlock: React.FC<ContentBlockProps> = ({
  block,
  isLast,
  isStreaming,
  isTyping,
}) => {
  const className = `content-block content-block-${block.type} ${
    isLast && isStreaming ? 'streaming' : ''
  } ${isLast && isTyping ? 'typing' : ''}`

  switch (block.type) {
    case 'code':
      return (
        <div className={`${className} relative`}>
          <SyntaxHighlighter
            language={block.language || 'text'}
            style={vscDarkPlus}
            customStyle={{
              margin: 0,
              borderRadius: '0.5rem',
              fontSize: '0.875rem',
            }}
          >
            {block.content}
          </SyntaxHighlighter>
          {isLast && isStreaming && (
            <StreamingCursor className="absolute bottom-2 right-2" />
          )}
        </div>
      )

    case 'heading':
      const level = Math.min(block.content.split('#').length - 1, 6)
      const HeadingTag = `h${level}` as keyof JSX.IntrinsicElements
      const headingContent = block.content.replace(/^#+\s*/, '')
      
      return (
        <HeadingTag className={`${className} font-bold mb-2 ${
          level === 1 ? 'text-2xl' :
          level === 2 ? 'text-xl' :
          level === 3 ? 'text-lg' :
          'text-base'
        }`}>
          {headingContent}
          {isLast && isStreaming && <StreamingCursor />}
        </HeadingTag>
      )

    case 'list':
      const listItems = block.content.split('\n').filter(line => line.trim())
      const isOrdered = /^\d+\./.test(listItems[0] || '')
      const ListTag = isOrdered ? 'ol' : 'ul'
      
      return (
        <ListTag className={`${className} ml-4 ${isOrdered ? 'list-decimal' : 'list-disc'}`}>
          {listItems.map((item, index) => {
            const itemContent = item.replace(/^(-|\*|\d+\.)\s*/, '')
            const isLastItem = index === listItems.length - 1
            
            return (
              <li key={index} className="mb-1">
                {itemContent}
                {isLastItem && isLast && isStreaming && <StreamingCursor />}
              </li>
            )
          })}
        </ListTag>
      )

    case 'quote':
      return (
        <blockquote className={`${className} border-l-4 border-gray-300 pl-4 italic text-gray-600`}>
          {block.content.replace(/^>\s*/gm, '')}
          {isLast && isStreaming && <StreamingCursor />}
        </blockquote>
      )

    case 'text':
    default:
      return (
        <div className={`${className} whitespace-pre-wrap`}>
          {block.content}
          {isLast && isStreaming && <StreamingCursor />}
        </div>
      )
  }
}
```

### **Step 3: Visual Indicators and Animations**

```typescript
// src/components/StreamingIndicators.tsx
import React from 'react'
import { Activity, Zap, Clock } from 'lucide-react'

export const TypingIndicator: React.FC<{ className?: string }> = ({ 
  className = '' 
}) => (
  <div className={`typing-indicator flex items-center gap-2 text-gray-500 ${className}`}>
    <div className="flex gap-1">
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" 
           style={{ animationDelay: '0ms' }} />
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" 
           style={{ animationDelay: '150ms' }} />
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" 
           style={{ animationDelay: '300ms' }} />
    </div>
    <span className="text-sm">Agent is typing...</span>
  </div>
)

export const StreamingCursor: React.FC<{ className?: string }> = ({ 
  className = '' 
}) => (
  <span className={`streaming-cursor inline-block w-0.5 h-4 bg-blue-500 animate-pulse ml-1 ${className}`} />
)

interface StreamingHeaderProps {
  agentName: string
  protocol: string
  isStreaming: boolean
  chunkCount: number
  wordsPerSecond: number
}

export const StreamingHeader: React.FC<StreamingHeaderProps> = ({
  agentName,
  protocol,
  isStreaming,
  chunkCount,
  wordsPerSecond,
}) => (
  <div className="streaming-header flex items-center justify-between mb-3 pb-2 border-b border-gray-200">
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${
          isStreaming ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
        }`} />
        <span className="font-semibold text-gray-800">{agentName}</span>
        <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
          {protocol.toUpperCase()}
        </span>
      </div>
    </div>
    
    {isStreaming && (
      <div className="streaming-stats flex items-center gap-4 text-xs text-gray-500">
        <div className="flex items-center gap-1">
          <Activity className="w-3 h-3" />
          <span>{chunkCount} chunks</span>
        </div>
        {wordsPerSecond > 0 && (
          <div className="flex items-center gap-1">
            <Zap className="w-3 h-3" />
            <span>{Math.round(wordsPerSecond)} wps</span>
          </div>
        )}
      </div>
    )}
  </div>
)

interface StreamingFooterProps {
  isComplete: boolean
  totalChunks: number
  streamDuration: number
}

export const StreamingFooter: React.FC<StreamingFooterProps> = ({
  isComplete,
  totalChunks,
  streamDuration,
}) => {
  if (!isComplete) return null

  return (
    <div className="streaming-footer mt-3 pt-2 border-t border-gray-200 flex items-center gap-4 text-xs text-gray-500">
      <div className="flex items-center gap-1">
        <Clock className="w-3 h-3" />
        <span>Completed in {(streamDuration / 1000).toFixed(1)}s</span>
      </div>
      <div>
        <span>{totalChunks} chunks received</span>
      </div>
      <div className="text-green-600 font-medium">
        ✓ Stream complete
      </div>
    </div>
  )
}
```

### **Step 4: Performance-Optimized Chunk Buffer**

```typescript
// src/hooks/useChunkBuffer.ts
import { useState, useEffect, useRef, useCallback } from 'react'

interface ChunkBufferConfig {
  maxBufferSize: number
  flushInterval: number // ms
  enableBatching: boolean
}

interface BufferedChunk {
  id: string
  content: string
  timestamp: Date
  processed: boolean
}

export const useChunkBuffer = (config: Partial<ChunkBufferConfig> = {}) => {
  const {
    maxBufferSize = 50,
    flushInterval = 100,
    enableBatching = true,
  } = config

  const [buffer, setBuffer] = useState<BufferedChunk[]>([])
  const [processedChunks, setProcessedChunks] = useState<BufferedChunk[]>([])
  const flushTimeoutRef = useRef<number>()
  const isFlushingRef = useRef(false)

  const addChunk = useCallback((content: string) => {
    const chunk: BufferedChunk = {
      id: `chunk-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      content,
      timestamp: new Date(),
      processed: false,
    }

    setBuffer(prev => {
      const newBuffer = [...prev, chunk]
      
      // Limit buffer size
      if (newBuffer.length > maxBufferSize) {
        return newBuffer.slice(-maxBufferSize)
      }
      
      return newBuffer
    })

    // Schedule flush if batching is enabled
    if (enableBatching && !isFlushingRef.current) {
      if (flushTimeoutRef.current) {
        clearTimeout(flushTimeoutRef.current)
      }
      
      flushTimeoutRef.current = window.setTimeout(() => {
        flushBuffer()
      }, flushInterval)
    }
  }, [maxBufferSize, enableBatching, flushInterval])

  const flushBuffer = useCallback(() => {
    if (isFlushingRef.current) return
    
    isFlushingRef.current = true
    
    setBuffer(currentBuffer => {
      if (currentBuffer.length === 0) {
        isFlushingRef.current = false
        return currentBuffer
      }

      // Mark all chunks as processed
      const processedBuffer = currentBuffer.map(chunk => ({
        ...chunk,
        processed: true,
      }))

      // Move to processed chunks
      setProcessedChunks(prev => [...prev, ...processedBuffer])

      isFlushingRef.current = false
      return []
    })
  }, [])

  const clearBuffer = useCallback(() => {
    setBuffer([])
    setProcessedChunks([])
    
    if (flushTimeoutRef.current) {
      clearTimeout(flushTimeoutRef.current)
    }
  }, [])

  const getAllChunks = useCallback(() => {
    return [...processedChunks, ...buffer]
  }, [processedChunks, buffer])

  // Auto-flush on unmount
  useEffect(() => {
    return () => {
      if (flushTimeoutRef.current) {
        clearTimeout(flushTimeoutRef.current)
      }
      if (buffer.length > 0 && !isFlushingRef.current) {
        flushBuffer()
      }
    }
  }, [buffer, flushBuffer])

  return {
    addChunk,
    flushBuffer,
    clearBuffer,
    getAllChunks,
    bufferedCount: buffer.length,
    processedCount: processedChunks.length,
    totalCount: buffer.length + processedChunks.length,
  }
}
```

### **Step 5: Integrated Streaming Chat Component**

```typescript
// src/components/StreamingChatMessage.tsx
import React, { useMemo } from 'react'
import { StreamingMessage } from './StreamingMessage'
import { useChunkBuffer } from '../hooks/useChunkBuffer'

interface StreamingChatMessageProps {
  message: {
    id: string
    agentName: string
    protocol: string
    chunks: string[]
    isStreaming: boolean
    timestamp: Date
  }
  className?: string
}

export const StreamingChatMessage: React.FC<StreamingChatMessageProps> = ({
  message,
  className = '',
}) => {
  const { getAllChunks } = useChunkBuffer({
    maxBufferSize: 100,
    flushInterval: 50,
    enableBatching: true,
  })

  // Convert string chunks to StreamingChunk objects
  const processedChunks = useMemo(() => {
    return message.chunks.map((content, index) => ({
      id: `${message.id}-chunk-${index}`,
      content,
      timestamp: new Date(message.timestamp.getTime() + index * 100),
      isComplete: !message.isStreaming || index < message.chunks.length - 1,
    }))
  }, [message.chunks, message.isStreaming, message.id, message.timestamp])

  const handleStreamComplete = (finalContent: string) => {
    console.log(`Stream completed for message ${message.id}:`, {
      finalLength: finalContent.length,
      chunkCount: processedChunks.length,
      agent: message.agentName,
    })
  }

  return (
    <div className={`streaming-chat-message mb-4 ${className}`}>
      <StreamingMessage
        chunks={processedChunks}
        isStreaming={message.isStreaming}
        agentName={message.agentName}
        protocol={message.protocol}
        onComplete={handleStreamComplete}
        className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm"
      />
    </div>
  )
}
```

### **Step 6: CSS Animations for Smooth Streaming**

```css
/* src/styles/streaming.css */

.streaming-message {
  position: relative;
  overflow: hidden;
}

.content-block {
  transition: all 0.2s ease-out;
}

.content-block.streaming {
  position: relative;
}

.content-block.typing {
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(59, 130, 246, 0.1) 50%, 
    transparent 100%
  );
  background-size: 200% 100%;
  animation: streaming-highlight 2s ease-in-out infinite;
}

@keyframes streaming-highlight {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.streaming-cursor {
  animation: cursor-blink 1s step-end infinite;
}

@keyframes cursor-blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.typing-indicator {
  animation: fade-in 0.3s ease-out;
}

.typing-indicator .animate-bounce:nth-child(1) {
  animation-delay: 0ms;
}

.typing-indicator .animate-bounce:nth-child(2) {
  animation-delay: 150ms;
}

.typing-indicator .animate-bounce:nth-child(3) {
  animation-delay: 300ms;
}

@keyframes fade-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.streaming-header {
  animation: slide-down 0.3s ease-out;
}

@keyframes slide-down {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.streaming-footer {
  animation: slide-up 0.3s ease-out;
}

@keyframes slide-up {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .streaming-header .streaming-stats {
    display: none;
  }
  
  .content-block code {
    font-size: 0.75rem;
  }
  
  .streaming-cursor {
    width: 2px;
    height: 1rem;
  }
}
```

## 🎯 **Usage Examples**

### **Integration with Streaming Hook**
```typescript
// In your chat component
const StreamingChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<StreamingChatMessageProps['message'][]>([])
  const { streamMessage, isStreaming } = useStreamingOrchestrator()

  const handleSendMessage = async (query: string) => {
    const messageId = `msg-${Date.now()}`
    
    // Add initial message
    setMessages(prev => [...prev, {
      id: messageId,
      agentName: 'Processing...',
      protocol: 'unknown',
      chunks: [],
      isStreaming: true,
      timestamp: new Date(),
    }])

    // Stream response
    await streamMessage(query, {
      onChunk: (chunk) => {
        setMessages(prev => prev.map(msg => 
          msg.id === messageId 
            ? { ...msg, chunks: [...msg.chunks, chunk] }
            : msg
        ))
      },
      onComplete: (response) => {
        setMessages(prev => prev.map(msg => 
          msg.id === messageId 
            ? { 
                ...msg, 
                agentName: response.agent_name,
                protocol: response.protocol,
                isStreaming: false 
              }
            : msg
        ))
      }
    })
  }

  return (
    <div className="streaming-chat">
      {messages.map(message => (
        <StreamingChatMessage
          key={message.id}
          message={message}
        />
      ))}
    </div>
  )
}
```

## 🎯 **Key Takeaways**

1. **Progressive rendering is key** - Display content as it arrives, don't wait
2. **Performance matters** - Use batching and efficient updates for high-frequency chunks
3. **Visual feedback is crucial** - Show typing indicators and streaming status
4. **Handle incomplete content gracefully** - Partial sentences should display well
5. **Smooth animations enhance UX** - Subtle transitions make streaming feel natural
6. **Mobile optimization is essential** - Streaming works on all device sizes
7. **Error boundaries prevent crashes** - Malformed chunks shouldn't break the UI

---

**Next**: [05-phase-tracking-indicators.md](./05-phase-tracking-indicators.md) - Advanced Loading States

**Previous**: [03-streaming-state-management.md](./03-streaming-state-management.md)