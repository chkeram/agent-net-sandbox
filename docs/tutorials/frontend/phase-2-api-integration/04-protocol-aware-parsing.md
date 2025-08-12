# Phase 2.4: Protocol-Aware Parsing - Handling Multi-Protocol Responses

## 🎯 **Learning Objectives**

By the end of this tutorial, you will:
- Understand the differences between A2A and ACP protocol response formats
- Implement unified parsing logic that handles both protocols transparently
- Build robust error handling for malformed or unexpected response structures
- Create type-safe interfaces for protocol-agnostic frontend components
- Handle edge cases and fallback scenarios in multi-protocol environments

## 🔍 **The Multi-Protocol Challenge**

Our Agent Network Sandbox supports multiple agent communication protocols:
- **A2A (Agent-to-Agent)**: Rich structured responses with "parts" arrays
- **ACP (Agent Communication Protocol)**: Simpler content-focused responses
- **Future protocols**: MCP and custom implementations

The challenge is creating a **unified interface** that works regardless of which protocol an agent uses.

### **Real-World Scenario**
```typescript
// User sends: "What is 2 + 2?"
// Could get back:

// A2A Response:
{
  protocol: "a2a",
  response_data: {
    raw_response: {
      result: {
        message: {
          parts: [
            { kind: "text", text: "The answer is " },
            { kind: "text", text: "4" }
          ]
        }
      }
    }
  }
}

// ACP Response:
{
  protocol: "acp", 
  response_data: {
    content: "The answer is 4",
    metadata: { agent_id: "acp-math" }
  }
}

// Both should display: "The answer is 4"
```

## 🛠️ **Building Protocol Detection**

### **Step 1: Protocol Detection Strategy**

```typescript
// src/services/protocolDetector.ts
export type SupportedProtocol = 'a2a' | 'acp' | 'mcp' | 'unknown'

export interface ProtocolDetectionResult {
  protocol: SupportedProtocol
  confidence: number
  reasons: string[]
}

export class ProtocolDetector {
  /**
   * Detect protocol from orchestrator response
   */
  static detect(orchestratorResponse: any): ProtocolDetectionResult {
    const reasons: string[] = []
    let protocol: SupportedProtocol = 'unknown'
    let confidence = 0

    // Check explicit protocol field first
    if (orchestratorResponse.protocol) {
      const explicitProtocol = orchestratorResponse.protocol.toLowerCase()
      if (['a2a', 'acp', 'mcp'].includes(explicitProtocol)) {
        protocol = explicitProtocol as SupportedProtocol
        confidence = 0.9
        reasons.push(`Explicit protocol field: ${explicitProtocol}`)
        return { protocol, confidence, reasons }
      }
    }

    // Check agent ID patterns
    const agentId = orchestratorResponse.agent_id?.toLowerCase() || ''
    if (agentId.includes('a2a')) {
      protocol = 'a2a'
      confidence = 0.7
      reasons.push(`Agent ID contains 'a2a': ${agentId}`)
    } else if (agentId.includes('acp')) {
      protocol = 'acp'
      confidence = 0.7
      reasons.push(`Agent ID contains 'acp': ${agentId}`)
    } else if (agentId.includes('mcp')) {
      protocol = 'mcp'
      confidence = 0.7
      reasons.push(`Agent ID contains 'mcp': ${agentId}`)
    }

    // Check response structure patterns
    const responseData = orchestratorResponse.response_data
    if (responseData) {
      // A2A typically has parts array structure
      if (this.hasA2AStructure(responseData)) {
        if (protocol === 'unknown' || confidence < 0.8) {
          protocol = 'a2a'
          confidence = 0.8
          reasons.push('Response has A2A parts structure')
        }
      }
      
      // ACP typically has direct content field
      if (this.hasACPStructure(responseData)) {
        if (protocol === 'unknown' || confidence < 0.8) {
          protocol = 'acp'
          confidence = 0.8
          reasons.push('Response has ACP content structure')
        }
      }
    }

    return { protocol, confidence, reasons }
  }

  private static hasA2AStructure(responseData: any): boolean {
    // Check for A2A patterns
    return !!(
      responseData.raw_response?.result?.message?.parts ||
      responseData.parts ||
      (responseData.message && responseData.message.parts)
    )
  }

  private static hasACPStructure(responseData: any): boolean {
    // Check for ACP patterns
    return !!(
      responseData.content !== undefined ||
      responseData.capabilities ||
      responseData.tools ||
      responseData.metadata
    )
  }
}
```

### **Step 2: Unified Response Interface**

```typescript
// src/types/unifiedResponse.ts
export interface UnifiedAgentResponse {
  // Core content (always available)
  textContent: string
  protocol: SupportedProtocol
  
  // Metadata (always available)
  agentInfo: {
    id: string
    name: string
    protocol: string
  }
  
  // Rich content (protocol-specific)
  richContent?: {
    // A2A specific
    parts?: Array<{
      kind: string
      text?: string
      code?: { language: string; content: string }
      reasoning?: string
    }>
    
    // ACP specific  
    toolCalls?: Array<{
      id: string
      tool: string
      function: string
      parameters: Record<string, any>
    }>
    
    capabilities?: Array<{
      name: string
      description: string
    }>
  }
  
  // Processing metadata
  confidence: number
  processingInfo: {
    parsingSuccess: boolean
    fallbackUsed: boolean
    warnings: string[]
    errors: string[]
  }
}
```

### **Step 3: Universal Response Parser**

```typescript
// src/services/universalParser.ts
import { ProtocolDetector } from './protocolDetector'
import { A2AParser } from './a2aParser'
import { ACPParser } from './acpParser'

export class UniversalResponseParser {
  /**
   * Parse any orchestrator response into unified format
   */
  static parse(orchestratorResponse: any): UnifiedAgentResponse {
    const detection = ProtocolDetector.detect(orchestratorResponse)
    const warnings: string[] = []
    const errors: string[] = []
    let textContent = ''
    let richContent: any = undefined
    let fallbackUsed = false

    try {
      switch (detection.protocol) {
        case 'a2a':
          const a2aResult = this.parseA2AResponse(orchestratorResponse)
          textContent = a2aResult.textContent
          richContent = { parts: a2aResult.parts }
          break
          
        case 'acp':
          const acpResult = this.parseACPResponse(orchestratorResponse)
          textContent = acpResult.textContent
          richContent = {
            toolCalls: acpResult.toolCalls,
            capabilities: acpResult.capabilities
          }
          break
          
        default:
          // Fallback parsing for unknown protocols
          const fallbackResult = this.parseUnknownResponse(orchestratorResponse)
          textContent = fallbackResult.textContent
          fallbackUsed = true
          warnings.push(`Unknown protocol ${detection.protocol}, using fallback parser`)
      }
    } catch (parseError) {
      // If protocol-specific parsing fails, use fallback
      errors.push(`Protocol parsing failed: ${parseError.message}`)
      const fallbackResult = this.parseUnknownResponse(orchestratorResponse)
      textContent = fallbackResult.textContent
      fallbackUsed = true
    }

    return {
      textContent: textContent || 'No content available',
      protocol: detection.protocol,
      agentInfo: {
        id: orchestratorResponse.agent_id || 'unknown',
        name: orchestratorResponse.agent_name || 'Unknown Agent',
        protocol: orchestratorResponse.protocol || detection.protocol,
      },
      richContent,
      confidence: detection.confidence,
      processingInfo: {
        parsingSuccess: errors.length === 0,
        fallbackUsed,
        warnings,
        errors,
      }
    }
  }

  private static parseA2AResponse(response: any) {
    // Delegate to specialized A2A parser
    return A2AParser.parse(response.response_data)
  }

  private static parseACPResponse(response: any) {
    // Delegate to specialized ACP parser  
    return ACPParser.parse(response.response_data)
  }

  private static parseUnknownResponse(response: any): { textContent: string } {
    // Generic fallback extraction
    const candidates = [
      response.response_data?.content,
      response.response_data?.text,
      response.response_data?.message,
      response.content,
      response.text,
      response.message,
    ]

    for (const candidate of candidates) {
      if (typeof candidate === 'string' && candidate.trim()) {
        return { textContent: candidate.trim() }
      }
    }

    // Last resort: stringify the response data
    try {
      return {
        textContent: JSON.stringify(response.response_data || response, null, 2)
      }
    } catch {
      return { textContent: 'Unable to extract content from response' }
    }
  }
}
```

## 🧪 **Integration with Orchestrator API**

### **Step 4: Update OrchestratorAPI Service**

```typescript
// src/services/orchestratorApi.ts - Updated with universal parsing
import { UniversalResponseParser } from './universalParser'

export class OrchestratorAPI {
  // ... existing methods ...

  /**
   * Process message with protocol-aware parsing
   */
  async processMessage(query: string): Promise<ProcessResponse> {
    const rawResponse = await this.makeRequest<any>('/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    })

    // Parse with universal parser
    const parsed = UniversalResponseParser.parse(rawResponse)
    
    // Log protocol detection info in development
    if (process.env.NODE_ENV === 'development') {
      console.log('🔍 Protocol Detection:', {
        detected: parsed.protocol,
        confidence: parsed.confidence,
        warnings: parsed.processingInfo.warnings,
        errors: parsed.processingInfo.errors,
      })
    }

    // Convert to ProcessResponse format
    return {
      request_id: rawResponse.request_id || 'unknown',
      agent_id: parsed.agentInfo.id,
      agent_name: parsed.agentInfo.name,
      protocol: parsed.protocol,
      content: parsed.textContent,
      confidence: rawResponse.confidence || parsed.confidence,
      success: parsed.processingInfo.parsingSuccess,
      duration_ms: rawResponse.duration_ms || 0,
      timestamp: rawResponse.timestamp || new Date().toISOString(),
      
      // Add parsing metadata
      _parsing: {
        fallbackUsed: parsed.processingInfo.fallbackUsed,
        warnings: parsed.processingInfo.warnings,
        richContent: parsed.richContent,
      }
    }
  }

  /**
   * Extract content using universal parser (backward compatibility)
   */
  public extractResponseContent(data: any): string {
    const parsed = UniversalResponseParser.parse(data)
    return parsed.textContent
  }

  /**
   * Get rich parsed response for advanced components
   */
  public parseResponse(data: any): UnifiedAgentResponse {
    return UniversalResponseParser.parse(data)
  }
}
```

### **Step 5: Protocol-Aware React Components**

```typescript
// src/components/ProtocolAwareMessage.tsx
import React from 'react'
import { UnifiedAgentResponse } from '../types/unifiedResponse'

interface ProtocolAwareMessageProps {
  response: UnifiedAgentResponse
  className?: string
}

export const ProtocolAwareMessage: React.FC<ProtocolAwareMessageProps> = ({
  response,
  className = '',
}) => {
  return (
    <div className={`protocol-aware-message ${className}`}>
      {/* Main content (always shown) */}
      <div className="message-content mb-4">
        <pre className="whitespace-pre-wrap">{response.textContent}</pre>
      </div>

      {/* Protocol-specific rich content */}
      {response.richContent && (
        <div className="rich-content mb-4">
          {response.protocol === 'a2a' && response.richContent.parts && (
            <A2ARichContent parts={response.richContent.parts} />
          )}
          
          {response.protocol === 'acp' && (
            <ACPRichContent 
              toolCalls={response.richContent.toolCalls} 
              capabilities={response.richContent.capabilities}
            />
          )}
        </div>
      )}

      {/* Agent and protocol info */}
      <div className="message-footer flex items-center justify-between text-xs text-gray-500">
        <div className="agent-info">
          <span className="font-medium">{response.agentInfo.name}</span>
          <span className="mx-2">•</span>
          <span className="protocol-badge px-2 py-1 bg-blue-100 text-blue-800 rounded">
            {response.protocol.toUpperCase()}
          </span>
        </div>
        
        <div className="parsing-info">
          {response.processingInfo.fallbackUsed && (
            <span className="fallback-indicator px-2 py-1 bg-yellow-100 text-yellow-800 rounded mr-2">
              Fallback Parser
            </span>
          )}
          <span>Confidence: {Math.round(response.confidence * 100)}%</span>
        </div>
      </div>

      {/* Debug info (development only) */}
      {process.env.NODE_ENV === 'development' && response.processingInfo.warnings.length > 0 && (
        <details className="mt-2 text-xs">
          <summary className="cursor-pointer text-yellow-600">
            ⚠️ Parsing Warnings ({response.processingInfo.warnings.length})
          </summary>
          <div className="mt-1 bg-yellow-50 p-2 rounded">
            {response.processingInfo.warnings.map((warning, i) => (
              <div key={i}>• {warning}</div>
            ))}
          </div>
        </details>
      )}
    </div>
  )
}

// A2A-specific rich content display
const A2ARichContent: React.FC<{ parts: any[] }> = ({ parts }) => (
  <div className="a2a-parts space-y-2">
    {parts.map((part, i) => (
      <div key={i} className={`part part-${part.kind} p-2 border-l-4 ${
        part.kind === 'code' ? 'border-green-400 bg-green-50' :
        part.kind === 'reasoning' ? 'border-purple-400 bg-purple-50' :
        'border-blue-400 bg-blue-50'
      }`}>
        <div className="part-type text-xs font-semibold text-gray-600 mb-1">
          {part.kind.toUpperCase()}
        </div>
        {part.text && <div className="part-text">{part.text}</div>}
        {part.code && (
          <pre className="part-code text-sm bg-gray-100 p-2 rounded">
            <code className={`language-${part.code.language}`}>
              {part.code.content}
            </code>
          </pre>
        )}
      </div>
    ))}
  </div>
)

// ACP-specific rich content display
const ACPRichContent: React.FC<{
  toolCalls?: any[]
  capabilities?: any[]
}> = ({ toolCalls, capabilities }) => (
  <div className="acp-content space-y-3">
    {toolCalls && toolCalls.length > 0 && (
      <div className="tool-calls">
        <h4 className="text-sm font-semibold mb-2">Tool Calls</h4>
        {toolCalls.map((call, i) => (
          <div key={i} className="tool-call p-2 bg-yellow-50 border-l-4 border-yellow-400">
            <div className="font-mono text-sm">
              {call.tool}.{call.function}({JSON.stringify(call.parameters)})
            </div>
          </div>
        ))}
      </div>
    )}
    
    {capabilities && capabilities.length > 0 && (
      <div className="capabilities">
        <h4 className="text-sm font-semibold mb-2">Agent Capabilities</h4>
        <div className="grid grid-cols-2 gap-2">
          {capabilities.map((cap, i) => (
            <div key={i} className="capability p-2 bg-gray-50 rounded">
              <div className="font-medium text-sm">{cap.name}</div>
              <div className="text-xs text-gray-600">{cap.description}</div>
            </div>
          ))}
        </div>
      </div>
    )}
  </div>
)
```

## 🧪 **Testing Protocol-Aware Parsing**

### **Step 6: Comprehensive Test Suite**

```typescript
// src/services/__tests__/universalParser.test.ts
import { UniversalResponseParser } from '../universalParser'

describe('UniversalResponseParser', () => {
  describe('A2A Response Parsing', () => {
    it('should parse A2A responses correctly', () => {
      const a2aResponse = {
        agent_id: 'a2a-math-agent',
        protocol: 'a2a',
        response_data: {
          raw_response: {
            result: {
              message: {
                parts: [
                  { kind: 'text', text: 'The answer is ' },
                  { kind: 'text', text: '42' }
                ]
              }
            }
          }
        }
      }

      const result = UniversalResponseParser.parse(a2aResponse)

      expect(result.protocol).toBe('a2a')
      expect(result.textContent).toContain('The answer is 42')
      expect(result.richContent?.parts).toHaveLength(2)
      expect(result.processingInfo.parsingSuccess).toBe(true)
      expect(result.processingInfo.fallbackUsed).toBe(false)
    })
  })

  describe('ACP Response Parsing', () => {
    it('should parse ACP responses correctly', () => {
      const acpResponse = {
        agent_id: 'acp-hello-world',
        protocol: 'acp',
        response_data: {
          content: 'Hello from ACP!',
          capabilities: [
            { name: 'greet', description: 'Provide greetings' }
          ]
        }
      }

      const result = UniversalResponseParser.parse(acpResponse)

      expect(result.protocol).toBe('acp')
      expect(result.textContent).toBe('Hello from ACP!')
      expect(result.richContent?.capabilities).toHaveLength(1)
      expect(result.processingInfo.parsingSuccess).toBe(true)
    })
  })

  describe('Protocol Detection', () => {
    it('should detect protocol from agent ID', () => {
      const response = {
        agent_id: 'a2a-unknown-agent',
        response_data: { content: 'Some content' }
      }

      const result = UniversalResponseParser.parse(response)

      expect(result.protocol).toBe('a2a')
      expect(result.confidence).toBeGreaterThan(0.5)
    })

    it('should use fallback for unknown protocols', () => {
      const unknownResponse = {
        agent_id: 'mystery-agent',
        response_data: { 
          some_weird_field: 'content here'
        }
      }

      const result = UniversalResponseParser.parse(unknownResponse)

      expect(result.protocol).toBe('unknown')
      expect(result.processingInfo.fallbackUsed).toBe(true)
      expect(result.textContent).toContain('some_weird_field')
    })
  })

  describe('Error Handling', () => {
    it('should gracefully handle malformed responses', () => {
      const malformedResponse = {
        agent_id: null,
        response_data: null
      }

      const result = UniversalResponseParser.parse(malformedResponse)

      expect(result.textContent).toBeTruthy()
      expect(result.processingInfo.fallbackUsed).toBe(true)
      expect(result.processingInfo.errors.length).toBeGreaterThan(0)
    })

    it('should handle empty responses', () => {
      const emptyResponse = {}

      const result = UniversalResponseParser.parse(emptyResponse)

      expect(result.textContent).toBe('Unable to extract content from response')
      expect(result.agentInfo.id).toBe('unknown')
      expect(result.protocol).toBe('unknown')
    })
  })
})
```

## 🎯 **Real-World Usage Examples**

### **Using in Components**
```typescript
// In your chat components
const { data: response } = useOrchestrator()

if (response) {
  const parsed = orchestratorApi.parseResponse(response)
  
  return (
    <ProtocolAwareMessage 
      response={parsed}
      className="message-item"
    />
  )
}
```

### **Streaming Integration**
```typescript
// Protocol-aware streaming
const handleStreamChunk = (chunk: string) => {
  // Parse each chunk to detect protocol early
  const parsed = UniversalResponseParser.parse({ 
    response_data: { content: chunk } 
  })
  
  setStreamContent(prev => prev + parsed.textContent)
}
```

## 🎯 **Key Takeaways**

1. **Protocol detection is probabilistic** - Use multiple signals for accuracy
2. **Always have fallback parsing** - Handle unknown or malformed responses
3. **Type safety matters** - Unified interfaces prevent runtime errors  
4. **Rich content is optional** - Basic text content should always work
5. **Debug information helps** - Show parsing confidence and warnings in development
6. **Test all protocols** - Don't assume one protocol works like another
7. **Performance considerations** - Protocol detection should be fast

---

**Next**: [05-error-handling-strategies.md](./05-error-handling-strategies.md) - Graceful Error Management

**Previous**: [03-hooks-for-api-state.md](./03-hooks-for-api-state.md)