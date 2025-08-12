# Protocol-Aware Parsing: A2A Response Handling

## 🎯 **Learning Objectives**

By the end of this tutorial, you will:
- Understand the A2A (Agent-to-Agent) protocol response structure
- Build robust parsers for A2A message formats
- Handle different A2A content types (text, code, structured data)
- Implement fallback strategies for malformed A2A responses
- Create type-safe A2A interfaces for better development experience

## 🌐 **What is the A2A Protocol?**

The **Agent-to-Agent (A2A) Protocol** is a standardized communication protocol for AI agents. It defines how agents exchange messages, capabilities, and structured data.

### **A2A Protocol Characteristics**
- **Structured Parts**: Messages are composed of typed "parts"
- **Rich Content Types**: Text, code, images, structured data, etc.
- **Metadata Support**: Confidence scores, reasoning, capabilities
- **Extensible**: New part types can be added without breaking compatibility

## 📋 **A2A Response Structure**

### **Raw A2A Response Format**

```json
{
  "jsonrpc": "2.0",
  "id": "request_123",
  "result": {
    "message": {
      "role": "assistant",
      "parts": [
        {
          "kind": "text",
          "text": "The answer to 2 + 2 is "
        },
        {
          "kind": "text", 
          "text": "4"
        },
        {
          "kind": "reasoning",
          "text": "This is basic arithmetic. I'm confident in this answer.",
          "confidence": 0.99
        }
      ]
    },
    "capabilities": ["math", "arithmetic"],
    "agent_info": {
      "name": "Math Agent",
      "version": "1.0.0"
    }
  }
}
```

### **Orchestrator-Wrapped A2A Response**

When our orchestrator processes an A2A agent response, it wraps it:

```json
{
  "request_id": "req_123",
  "agent_id": "a2a-math-agent",
  "agent_name": "Math Agent", 
  "protocol": "a2a",
  "confidence": 0.95,
  "reasoning": "User asked for basic arithmetic - Math Agent is perfect for this",
  "response_data": {
    "raw_response": {
      "message": {
        "role": "assistant",
        "parts": [
          {
            "kind": "text",
            "text": "The answer to 2 + 2 is 4"
          }
        ]
      }
    }
  },
  "success": true,
  "duration_ms": 142,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🛠️ **Building A2A Response Parser**

### **Step 1: Type Definitions**

```typescript
// src/types/a2a.ts

// Core A2A part types
export type A2APartKind = 
  | 'text' 
  | 'code' 
  | 'image' 
  | 'reasoning'
  | 'structured_data'
  | 'capability'
  | 'metadata';

// Base part structure
export interface A2ABasePart {
  kind: A2APartKind;
  metadata?: Record<string, any>;
}

// Specific part types
export interface A2ATextPart extends A2ABasePart {
  kind: 'text';
  text: string;
}

export interface A2ACodePart extends A2ABasePart {
  kind: 'code';
  text: string;
  language?: string;
  filename?: string;
}

export interface A2AImagePart extends A2ABasePart {
  kind: 'image';
  url?: string;
  data?: string; // base64 encoded
  alt_text?: string;
  format?: 'png' | 'jpg' | 'gif' | 'svg';
}

export interface A2AReasoningPart extends A2ABasePart {
  kind: 'reasoning';
  text: string;
  confidence?: number;
  reasoning_type?: 'explanation' | 'justification' | 'uncertainty';
}

export interface A2AStructuredDataPart extends A2ABasePart {
  kind: 'structured_data';
  data: any;
  schema?: string;
  format?: 'json' | 'yaml' | 'xml';
}

// Union type for all parts
export type A2APart = 
  | A2ATextPart 
  | A2ACodePart 
  | A2AImagePart 
  | A2AReasoningPart 
  | A2AStructuredDataPart;

// A2A message structure
export interface A2AMessage {
  role: 'user' | 'assistant';
  parts: A2APart[];
}

// Full A2A response
export interface A2AResponse {
  jsonrpc: '2.0';
  id: string | number;
  result?: {
    message: A2AMessage;
    capabilities?: string[];
    agent_info?: {
      name: string;
      version?: string;
      description?: string;
    };
  };
  error?: {
    code: number;
    message: string;
    data?: any;
  };
}

// Parsed content for UI display
export interface ParsedA2AContent {
  textContent: string;
  codeBlocks: Array<{
    code: string;
    language?: string;
    filename?: string;
  }>;
  images: Array<{
    url?: string;
    data?: string;
    altText?: string;
    format?: string;
  }>;
  reasoning: Array<{
    text: string;
    confidence?: number;
    type?: string;
  }>;
  structuredData: Array<{
    data: any;
    schema?: string;
    format?: string;
  }>;
  capabilities: string[];
}
```

### **Step 2: Core A2A Parser Class**

```typescript
// src/services/a2aParser.ts
import type { 
  A2APart, 
  A2AResponse, 
  A2AMessage,
  ParsedA2AContent,
  A2ATextPart,
  A2ACodePart,
  A2AImagePart,
  A2AReasoningPart,
  A2AStructuredDataPart 
} from '../types/a2a';

export class A2AResponseParser {
  /**
   * Parse orchestrator response containing A2A data
   */
  static parseOrchestratorResponse(orchestratorResponse: any): ParsedA2AContent | null {
    try {
      // Extract A2A response from orchestrator wrapper
      const responseData = orchestratorResponse.response_data;
      if (!responseData) {
        console.warn('No response_data in orchestrator response');
        return null;
      }

      // Handle different possible structures
      let a2aResponse: A2AResponse | null = null;
      
      if (responseData.raw_response) {
        // Direct A2A response wrapped in raw_response
        a2aResponse = responseData.raw_response;
      } else if (responseData.message || responseData.parts) {
        // A2A message structure directly in response_data
        a2aResponse = {
          jsonrpc: '2.0',
          id: orchestratorResponse.request_id || 'unknown',
          result: {
            message: responseData.message || { role: 'assistant', parts: responseData.parts || [] }
          }
        };
      } else {
        console.warn('Unrecognized A2A response structure:', responseData);
        return null;
      }

      return this.parseA2AResponse(a2aResponse);
    } catch (error) {
      console.error('Failed to parse orchestrator A2A response:', error);
      return null;
    }
  }

  /**
   * Parse raw A2A response
   */
  static parseA2AResponse(response: A2AResponse): ParsedA2AContent | null {
    try {
      if (response.error) {
        console.error('A2A response contains error:', response.error);
        return null;
      }

      if (!response.result?.message) {
        console.warn('A2A response missing result.message');
        return null;
      }

      return this.parseA2AMessage(response.result.message, response.result);
    } catch (error) {
      console.error('Failed to parse A2A response:', error);
      return null;
    }
  }

  /**
   * Parse A2A message into structured content
   */
  static parseA2AMessage(message: A2AMessage, context?: any): ParsedA2AContent {
    const parsed: ParsedA2AContent = {
      textContent: '',
      codeBlocks: [],
      images: [],
      reasoning: [],
      structuredData: [],
      capabilities: context?.capabilities || [],
    };

    if (!message.parts || !Array.isArray(message.parts)) {
      console.warn('A2A message missing parts array');
      return parsed;
    }

    // Process each part
    for (const part of message.parts) {
      try {
        this.processPart(part, parsed);
      } catch (error) {
        console.warn('Failed to process A2A part:', part, error);
        // Continue processing other parts
      }
    }

    return parsed;
  }

  /**
   * Process individual A2A part
   */
  private static processPart(part: A2APart, parsed: ParsedA2AContent): void {
    if (!part || typeof part !== 'object' || !part.kind) {
      console.warn('Invalid A2A part:', part);
      return;
    }

    switch (part.kind) {
      case 'text':
        this.processTextPart(part as A2ATextPart, parsed);
        break;
      
      case 'code':
        this.processCodePart(part as A2ACodePart, parsed);
        break;
      
      case 'image':
        this.processImagePart(part as A2AImagePart, parsed);
        break;
      
      case 'reasoning':
        this.processReasoningPart(part as A2AReasoningPart, parsed);
        break;
      
      case 'structured_data':
        this.processStructuredDataPart(part as A2AStructuredDataPart, parsed);
        break;
      
      default:
        console.warn('Unknown A2A part kind:', part.kind);
        // Try to extract text if available
        if ('text' in part && typeof part.text === 'string') {
          parsed.textContent += part.text;
        }
    }
  }

  private static processTextPart(part: A2ATextPart, parsed: ParsedA2AContent): void {
    if (part.text && typeof part.text === 'string') {
      parsed.textContent += part.text;
    }
  }

  private static processCodePart(part: A2ACodePart, parsed: ParsedA2AContent): void {
    if (part.text && typeof part.text === 'string') {
      parsed.codeBlocks.push({
        code: part.text,
        language: part.language,
        filename: part.filename,
      });
      
      // Also add to text content with formatting
      const languageTag = part.language ? `\`\`\`${part.language}\n` : '```\n';
      parsed.textContent += `\n${languageTag}${part.text}\n\`\`\`\n`;
    }
  }

  private static processImagePart(part: A2AImagePart, parsed: ParsedA2AContent): void {
    parsed.images.push({
      url: part.url,
      data: part.data,
      altText: part.alt_text,
      format: part.format,
    });
    
    // Add placeholder to text content
    const altText = part.alt_text || 'Image';
    parsed.textContent += `\n![${altText}](${part.url || 'data:image'})\n`;
  }

  private static processReasoningPart(part: A2AReasoningPart, parsed: ParsedA2AContent): void {
    if (part.text && typeof part.text === 'string') {
      parsed.reasoning.push({
        text: part.text,
        confidence: part.confidence,
        type: part.reasoning_type,
      });
    }
  }

  private static processStructuredDataPart(part: A2AStructuredDataPart, parsed: ParsedA2AContent): void {
    parsed.structuredData.push({
      data: part.data,
      schema: part.schema,
      format: part.format,
    });
    
    // Add formatted data to text content
    try {
      const formatted = part.format === 'json' 
        ? JSON.stringify(part.data, null, 2)
        : String(part.data);
      parsed.textContent += `\n\`\`\`${part.format || 'data'}\n${formatted}\n\`\`\`\n`;
    } catch (error) {
      parsed.textContent += '\n[Structured Data]\n';
    }
  }
}
```

### **Step 3: Integration with Orchestrator API**

```typescript
// src/services/orchestratorApi.ts - Enhanced with A2A parsing
import { A2AResponseParser } from './a2aParser';

export class OrchestratorAPI {
  // ... existing methods ...

  /**
   * Extract content from A2A protocol responses
   */
  public extractA2AContent(orchestratorResponse: any): string {
    // Try A2A-specific parsing first
    const parsed = A2AResponseParser.parseOrchestratorResponse(orchestratorResponse);
    
    if (parsed) {
      // Return combined text content
      let content = parsed.textContent.trim();
      
      // Add reasoning if available and not already included
      if (parsed.reasoning.length > 0 && !content.includes(parsed.reasoning[0].text)) {
        const reasoningText = parsed.reasoning
          .map(r => r.text)
          .join(' ');
        
        if (reasoningText && !content.toLowerCase().includes(reasoningText.toLowerCase())) {
          content += `\n\n*Reasoning: ${reasoningText}*`;
        }
      }
      
      return content || 'No content available';
    }
    
    // Fallback to generic extraction
    return this.extractGenericContent(orchestratorResponse);
  }

  /**
   * Enhanced response parsing with A2A support
   */
  public extractResponseContent(data: any): string {
    const protocol = data.protocol?.toLowerCase();
    
    if (protocol === 'a2a') {
      return this.extractA2AContent(data);
    }
    
    // Handle other protocols...
    return this.extractGenericContent(data);
  }

  private extractGenericContent(data: any): string {
    // Existing fallback logic
    const candidates = [
      data.content,
      data.response_data?.content,
      data.response_data?.text,
      data.response_data?.message,
      data.text,
      data.message,
    ];
    
    for (const candidate of candidates) {
      if (typeof candidate === 'string' && candidate.trim()) {
        return candidate.trim();
      }
    }
    
    return 'No response content available';
  }
}
```

### **Step 4: React Component for A2A Content Display**

```typescript
// src/components/A2AContent.tsx
import React from 'react';
import { A2AResponseParser, ParsedA2AContent } from '../services/a2aParser';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface A2AContentProps {
  orchestratorResponse: any;
  className?: string;
}

export const A2AContent: React.FC<A2AContentProps> = ({ 
  orchestratorResponse, 
  className = '' 
}) => {
  const parsed = React.useMemo(() => {
    return A2AResponseParser.parseOrchestratorResponse(orchestratorResponse);
  }, [orchestratorResponse]);

  if (!parsed) {
    return (
      <div className={`text-gray-500 italic ${className}`}>
        Unable to parse A2A response
      </div>
    );
  }

  return (
    <div className={`a2a-content ${className}`}>
      {/* Text Content */}
      {parsed.textContent && (
        <div className="prose prose-sm max-w-none">
          {parsed.textContent.split('\n').map((line, index) => (
            <p key={index} className="mb-2">
              {line}
            </p>
          ))}
        </div>
      )}

      {/* Code Blocks */}
      {parsed.codeBlocks.map((codeBlock, index) => (
        <div key={index} className="mt-4">
          {codeBlock.filename && (
            <div className="bg-gray-100 px-3 py-1 text-sm font-mono text-gray-700 border-b">
              {codeBlock.filename}
            </div>
          )}
          <SyntaxHighlighter
            language={codeBlock.language || 'text'}
            style={tomorrow}
            className="rounded-b-md"
          >
            {codeBlock.code}
          </SyntaxHighlighter>
        </div>
      ))}

      {/* Images */}
      {parsed.images.map((image, index) => (
        <div key={index} className="mt-4">
          <img
            src={image.url || `data:image/${image.format};base64,${image.data}`}
            alt={image.altText || 'A2A Image'}
            className="max-w-full h-auto rounded-lg shadow-sm"
          />
          {image.altText && (
            <p className="text-sm text-gray-600 mt-2 italic">
              {image.altText}
            </p>
          )}
        </div>
      ))}

      {/* Structured Data */}
      {parsed.structuredData.map((data, index) => (
        <div key={index} className="mt-4">
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-semibold mb-2">Structured Data</h4>
            <SyntaxHighlighter
              language={data.format || 'json'}
              style={tomorrow}
              className="rounded"
            >
              {typeof data.data === 'string' 
                ? data.data 
                : JSON.stringify(data.data, null, 2)
              }
            </SyntaxHighlighter>
          </div>
        </div>
      ))}

      {/* Reasoning (if not already included in text) */}
      {parsed.reasoning.length > 0 && (
        <div className="mt-4 bg-blue-50 p-3 rounded-lg border-l-4 border-blue-400">
          <h4 className="font-semibold text-blue-800 mb-2">Reasoning</h4>
          {parsed.reasoning.map((reasoning, index) => (
            <div key={index} className="mb-2 last:mb-0">
              <p className="text-blue-700">{reasoning.text}</p>
              {reasoning.confidence && (
                <p className="text-sm text-blue-600 mt-1">
                  Confidence: {Math.round(reasoning.confidence * 100)}%
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Capabilities */}
      {parsed.capabilities.length > 0 && (
        <div className="mt-4">
          <h4 className="font-semibold mb-2 text-sm">Agent Capabilities</h4>
          <div className="flex flex-wrap gap-2">
            {parsed.capabilities.map((capability, index) => (
              <span
                key={index}
                className="inline-block px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs"
              >
                {capability}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
```

## 🧪 **Testing A2A Parser**

### **Unit Tests**

```typescript
// src/services/__tests__/a2aParser.test.ts
import { A2AResponseParser } from '../a2aParser';

describe('A2AResponseParser', () => {
  describe('parseA2AMessage', () => {
    it('should parse simple text parts', () => {
      const message = {
        role: 'assistant' as const,
        parts: [
          { kind: 'text' as const, text: 'Hello ' },
          { kind: 'text' as const, text: 'world!' },
        ],
      };

      const result = A2AResponseParser.parseA2AMessage(message);

      expect(result.textContent).toBe('Hello world!');
      expect(result.codeBlocks).toHaveLength(0);
      expect(result.images).toHaveLength(0);
    });

    it('should parse code parts', () => {
      const message = {
        role: 'assistant' as const,
        parts: [
          {
            kind: 'code' as const,
            text: 'console.log("Hello");',
            language: 'javascript',
            filename: 'hello.js',
          },
        ],
      };

      const result = A2AResponseParser.parseA2AMessage(message);

      expect(result.codeBlocks).toHaveLength(1);
      expect(result.codeBlocks[0]).toEqual({
        code: 'console.log("Hello");',
        language: 'javascript',
        filename: 'hello.js',
      });
      expect(result.textContent).toContain('```javascript');
    });

    it('should parse reasoning parts', () => {
      const message = {
        role: 'assistant' as const,
        parts: [
          {
            kind: 'reasoning' as const,
            text: 'This is my reasoning',
            confidence: 0.95,
            reasoning_type: 'explanation' as const,
          },
        ],
      };

      const result = A2AResponseParser.parseA2AMessage(message);

      expect(result.reasoning).toHaveLength(1);
      expect(result.reasoning[0]).toEqual({
        text: 'This is my reasoning',
        confidence: 0.95,
        type: 'explanation',
      });
    });

    it('should handle malformed parts gracefully', () => {
      const message = {
        role: 'assistant' as const,
        parts: [
          null,
          { kind: 'text' as const, text: 'Valid text' },
          { invalid: 'part' },
          { kind: 'unknown_kind' as any, text: 'Unknown but has text' },
        ],
      };

      const result = A2AResponseParser.parseA2AMessage(message);

      expect(result.textContent).toBe('Valid textUnknown but has text');
    });
  });

  describe('parseOrchestratorResponse', () => {
    it('should parse orchestrator-wrapped A2A response', () => {
      const orchestratorResponse = {
        request_id: 'test_123',
        protocol: 'a2a',
        response_data: {
          raw_response: {
            message: {
              role: 'assistant',
              parts: [
                { kind: 'text', text: 'The answer is 42' },
              ],
            },
          },
        },
      };

      const result = A2AResponseParser.parseOrchestratorResponse(orchestratorResponse);

      expect(result).not.toBeNull();
      expect(result!.textContent).toBe('The answer is 42');
    });

    it('should handle missing response_data', () => {
      const orchestratorResponse = {
        request_id: 'test_123',
        protocol: 'a2a',
      };

      const result = A2AResponseParser.parseOrchestratorResponse(orchestratorResponse);

      expect(result).toBeNull();
    });
  });
});
```

### **Integration Tests**

```typescript
// src/services/__tests__/a2aIntegration.test.ts
describe('A2A Integration', () => {
  it('should handle real A2A math agent response', () => {
    const realResponse = {
      "request_id": "req_math_123",
      "agent_id": "a2a-math-agent",
      "protocol": "a2a",
      "response_data": {
        "raw_response": {
          "jsonrpc": "2.0",
          "id": "math_request_1",
          "result": {
            "message": {
              "role": "assistant",
              "parts": [
                {
                  "kind": "text",
                  "text": "To solve 15 * 23, I'll multiply:"
                },
                {
                  "kind": "code",
                  "text": "15 * 23 = 345",
                  "language": "math"
                },
                {
                  "kind": "reasoning",
                  "text": "This is straightforward multiplication",
                  "confidence": 0.99
                }
              ]
            }
          }
        }
      }
    };

    const parsed = A2AResponseParser.parseOrchestratorResponse(realResponse);

    expect(parsed).not.toBeNull();
    expect(parsed!.textContent).toContain('To solve 15 * 23');
    expect(parsed!.codeBlocks).toHaveLength(1);
    expect(parsed!.reasoning).toHaveLength(1);
    expect(parsed!.reasoning[0].confidence).toBe(0.99);
  });
});
```

## 🔧 **Error Handling and Fallbacks**

### **Robust Error Handling**

```typescript
// Enhanced parser with comprehensive error handling
export class RobustA2AParser extends A2AResponseParser {
  static parseWithFallbacks(orchestratorResponse: any): {
    content: string;
    parsed: ParsedA2AContent | null;
    errors: string[];
  } {
    const errors: string[] = [];
    let parsed: ParsedA2AContent | null = null;
    let content = '';

    try {
      // Primary parsing attempt
      parsed = this.parseOrchestratorResponse(orchestratorResponse);
      
      if (parsed) {
        content = parsed.textContent || 'No text content available';
      } else {
        errors.push('Failed to parse A2A response');
      }
    } catch (error) {
      errors.push(`A2A parsing error: ${error.message}`);
    }

    // Fallback extraction if parsing failed
    if (!content && orchestratorResponse.response_data) {
      content = this.extractFallbackContent(orchestratorResponse.response_data, errors);
    }

    // Last resort fallback
    if (!content) {
      content = 'Unable to extract content from A2A response';
      errors.push('All parsing methods failed');
    }

    return { content, parsed, errors };
  }

  private static extractFallbackContent(responseData: any, errors: string[]): string {
    // Try various fallback extraction methods
    const fallbackMethods = [
      () => this.extractFromRawResponse(responseData.raw_response),
      () => this.extractFromParts(responseData.parts || responseData.message?.parts),
      () => this.extractFromText(responseData.text || responseData.content),
      () => JSON.stringify(responseData, null, 2),
    ];

    for (const method of fallbackMethods) {
      try {
        const result = method();
        if (result && typeof result === 'string' && result.trim()) {
          return result.trim();
        }
      } catch (error) {
        errors.push(`Fallback method failed: ${error.message}`);
      }
    }

    return '';
  }

  private static extractFromRawResponse(rawResponse: any): string {
    if (!rawResponse?.result?.message?.parts) return '';
    
    return rawResponse.result.message.parts
      .filter((part: any) => part && typeof part.text === 'string')
      .map((part: any) => part.text)
      .join(' ');
  }

  private static extractFromParts(parts: any[]): string {
    if (!Array.isArray(parts)) return '';
    
    return parts
      .filter(part => part && typeof part.text === 'string')
      .map(part => part.text)
      .join(' ');
  }

  private static extractFromText(text: any): string {
    return typeof text === 'string' ? text : '';
  }
}
```

## 🎯 **Key Takeaways**

1. **A2A uses structured parts** - Text, code, images, reasoning are separate components
2. **Type safety is crucial** - Define interfaces for all A2A structures
3. **Parse progressively** - Handle each part type specifically
4. **Always include fallbacks** - Real-world responses may be malformed
5. **Separate parsing from display** - Parse once, render in multiple ways
6. **Test with real data** - Mock responses should match actual agent output
7. **Handle partial failures** - Extract what you can, gracefully handle errors

---

**Next**: [02-acp-response-handling.md](./02-acp-response-handling.md) - ACP Protocol Response Parsing

**Previous**: [Phase 3: Streaming State Management](../phase-3-streaming/03-streaming-state-management.md)