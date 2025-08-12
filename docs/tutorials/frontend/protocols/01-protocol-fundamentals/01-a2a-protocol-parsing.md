# Protocol-Aware Parsing: A2A Protocol Implementation

## 🎯 **Learning Objectives**

By the end of this tutorial, you will:
- Understand the A2A (Agent-to-Agent) protocol structure and message formats
- Implement robust parsing for A2A streaming and regular responses
- Handle A2A-specific data structures like "parts" arrays and message roles
- Build error-tolerant parsing that gracefully handles malformed responses
- Create type-safe A2A integration with full TypeScript support

## 🔍 **A2A Protocol Overview**

The **A2A (Agent-to-Agent) Protocol** is a standardized communication format designed for AI agent interactions. Our implementation integrates with the official A2A Python SDK.

### **Key Characteristics**
- **Message Parts**: Content split into structured "parts" with types
- **Role-Based**: Clear separation between user and agent messages  
- **Streaming Support**: Designed for real-time chunk-by-chunk delivery
- **Extensible**: Supports text, code, images, and custom content types

### **A2A Message Structure**
```json
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {
          "kind": "text",
          "text": "What is 2 + 2?"
        }
      ]
    }
  },
  "id": "request_123"
}
```

## 📦 **A2A Response Formats**

### **Regular API Response**
```json
{
  "request_id": "req_123",
  "agent_id": "a2a-math-agent",
  "agent_name": "A2A Math Agent",
  "protocol": "a2a",
  "response_data": {
    "raw_response": {
      "parts": [
        {
          "kind": "text", 
          "text": "The answer is "
        },
        {
          "kind": "text",
          "text": "4"
        }
      ]
    }
  },
  "confidence": 0.95,
  "reasoning": "Math query detected - routing to specialized math agent",
  "success": true
}
```

### **Streaming Response Chunks**
```json
{
  "event": "response_chunk",
  "protocol": "a2a", 
  "response_data": {
    "raw_response": {
      "parts": [
        {
          "kind": "text",
          "text": "The"
        }
      ]
    }
  }
}
```

## 🛠️ **A2A Parser Implementation**

### **Step 1: Type Definitions**

```typescript
// src/types/a2a.ts

export interface A2APart {
  kind: 'text' | 'code' | 'image' | 'tool_call' | 'tool_result';
  text?: string;
  code?: {
    language?: string;
    content: string;
  };
  image?: {
    url: string;
    alt_text?: string;
  };
  tool_call?: {
    name: string;
    arguments: Record<string, any>;
  };
  tool_result?: {
    tool_call_id: string;
    result: any;
  };
}

export interface A2AMessage {
  role: 'user' | 'assistant' | 'system';
  parts: A2APart[];
}

export interface A2AResponse {
  raw_response: A2AMessage;
}

export interface A2AStreamChunk {
  event: 'response_chunk';
  protocol: 'a2a';
  response_data: A2AResponse;
}
```

### **Step 2: Core A2A Parser Class**

```typescript
// src/services/a2aParser.ts

export class A2AParser {
  /**
   * Extract clean text content from A2A response data
   */
  static extractContent(responseData: any): string {
    try {
      // Handle both regular and streaming response formats
      const rawResponse = responseData?.raw_response;
      
      if (!rawResponse || !Array.isArray(rawResponse.parts)) {
        throw new Error('Invalid A2A response: missing parts array');
      }
      
      // Extract text content from all text parts
      const textParts = rawResponse.parts
        .filter((part: A2APart) => this.isTextPart(part))
        .map((part: A2APart) => part.text)
        .filter(Boolean); // Remove empty/null values
      
      if (textParts.length === 0) {
        // No text parts found, try to extract from other part types
        return this.extractFromNonTextParts(rawResponse.parts);
      }
      
      return textParts.join('').trim();
      
    } catch (error) {
      console.warn('A2A parsing failed:', error);
      return this.fallbackExtraction(responseData);
    }
  }
  
  /**
   * Check if a part is a text part
   */
  private static isTextPart(part: any): part is A2APart & { kind: 'text' } {
    return part && (
      part.kind === 'text' || 
      (!part.kind && part.text) // Handle parts without explicit kind
    );
  }
  
  /**
   * Extract content from non-text parts when no text parts available
   */
  private static extractFromNonTextParts(parts: A2APart[]): string {
    const contentParts: string[] = [];
    
    for (const part of parts) {
      switch (part.kind) {
        case 'code':
          if (part.code?.content) {
            contentParts.push(`\`\`\`${part.code.language || ''}\n${part.code.content}\n\`\`\``);
          }
          break;
          
        case 'tool_call':
          if (part.tool_call) {
            contentParts.push(`Tool Call: ${part.tool_call.name}`);
          }
          break;
          
        case 'tool_result':
          if (part.tool_result?.result) {
            const result = typeof part.tool_result.result === 'string' 
              ? part.tool_result.result 
              : JSON.stringify(part.tool_result.result);
            contentParts.push(`Result: ${result}`);
          }
          break;
          
        case 'image':
          if (part.image) {
            contentParts.push(`Image: ${part.image.alt_text || part.image.url}`);
          }
          break;
      }
    }
    
    return contentParts.join('\n\n').trim();
  }
  
  /**
   * Fallback extraction for malformed responses
   */
  private static fallbackExtraction(responseData: any): string {
    // Try to find any text content in the response
    const searchForText = (obj: any): string[] => {
      const texts: string[] = [];
      
      if (typeof obj === 'string') {
        return [obj];
      }
      
      if (typeof obj === 'object' && obj !== null) {
        for (const [key, value] of Object.entries(obj)) {
          if (key === 'text' && typeof value === 'string') {
            texts.push(value);
          } else {
            texts.push(...searchForText(value));
          }
        }
      }
      
      return texts;
    };
    
    const foundTexts = searchForText(responseData);
    return foundTexts.join(' ').trim() || 'No content available';
  }
  
  /**
   * Parse streaming chunk specifically
   */
  static parseStreamChunk(chunkData: any): string {
    if (!chunkData || chunkData.protocol !== 'a2a') {
      throw new Error('Invalid A2A stream chunk');
    }
    
    return this.extractContent(chunkData.response_data);
  }
  
  /**
   * Validate A2A response structure
   */
  static validateResponse(responseData: any): boolean {
    try {
      if (!responseData || !responseData.raw_response) {
        return false;
      }
      
      const rawResponse = responseData.raw_response;
      
      // Must have parts array
      if (!Array.isArray(rawResponse.parts)) {
        return false;
      }
      
      // Each part must have a valid structure
      for (const part of rawResponse.parts) {
        if (!part || typeof part !== 'object') {
          return false;
        }
        
        // Must have either kind or text property
        if (!part.kind && !part.text) {
          return false;
        }
      }
      
      return true;
      
    } catch {
      return false;
    }
  }
  
  /**
   * Get detailed part information for debugging
   */
  static analyzeResponse(responseData: any): {
    isValid: boolean;
    partsCount: number;
    partTypes: string[];
    textPartsCount: number;
    totalTextLength: number;
    errors: string[];
  } {
    const analysis = {
      isValid: false,
      partsCount: 0,
      partTypes: [] as string[],
      textPartsCount: 0,
      totalTextLength: 0,
      errors: [] as string[],
    };
    
    try {
      const rawResponse = responseData?.raw_response;
      
      if (!rawResponse) {
        analysis.errors.push('Missing raw_response');
        return analysis;
      }
      
      if (!Array.isArray(rawResponse.parts)) {
        analysis.errors.push('Parts is not an array');
        return analysis;
      }
      
      analysis.partsCount = rawResponse.parts.length;
      analysis.isValid = true;
      
      for (const part of rawResponse.parts) {
        if (part.kind) {
          analysis.partTypes.push(part.kind);
        } else {
          analysis.partTypes.push('unknown');
        }
        
        if (this.isTextPart(part)) {
          analysis.textPartsCount += 1;
          analysis.totalTextLength += (part.text?.length || 0);
        }
      }
      
      // Remove duplicate part types
      analysis.partTypes = Array.from(new Set(analysis.partTypes));
      
    } catch (error) {
      analysis.errors.push(`Analysis failed: ${error.message}`);
    }
    
    return analysis;
  }
}
```

### **Step 3: Integration with Orchestrator API**

```typescript
// src/services/orchestratorApi.ts (A2A-specific additions)

import { A2AParser } from './a2aParser';

class OrchestratorAPI {
  // ... existing methods ...
  
  /**
   * Enhanced content extraction with A2A support
   */
  public extractResponseContent(data: any): string {
    const protocol = data.protocol?.toLowerCase();
    
    // Use specialized A2A parser
    if (protocol === 'a2a') {
      return A2AParser.extractContent(data.response_data);
    }
    
    // Fall back to generic parsing for other protocols
    return this.genericContentExtraction(data);
  }
  
  /**
   * Validate response before parsing
   */
  private validateA2AResponse(data: any): void {
    if (!A2AParser.validateResponse(data.response_data)) {
      const analysis = A2AParser.analyzeResponse(data.response_data);
      throw new Error(
        `Invalid A2A response: ${analysis.errors.join(', ')}. ` +
        `Parts: ${analysis.partsCount}, Text parts: ${analysis.textPartsCount}`
      );
    }
  }
  
  /**
   * Process message with A2A-specific handling
   */
  async processMessage(query: string): Promise<ProcessResponse> {
    const response = await this.makeRequest<any>('/process', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
    
    // Validate A2A responses before processing
    if (response.protocol?.toLowerCase() === 'a2a') {
      this.validateA2AResponse(response);
    }
    
    return this.parseProcessResponse(response);
  }
}
```

### **Step 4: Streaming Integration**

```typescript
// src/services/streamingApi.ts (A2A streaming support)

import { A2AParser } from './a2aParser';

class StreamingAPI {
  // ... existing methods ...
  
  private handleResponseChunk(chunkEvent: ResponseChunkEvent): void {
    if (!chunkEvent.response_data || !chunkEvent.protocol) {
      console.warn('Response chunk missing data or protocol');
      return;
    }
    
    try {
      let extractedContent: string;
      
      // Use protocol-specific parsing
      if (chunkEvent.protocol.toLowerCase() === 'a2a') {
        extractedContent = A2AParser.parseStreamChunk(chunkEvent);
      } else {
        // Use generic orchestrator API parsing
        extractedContent = orchestratorApi.extractResponseContent({
          response_data: chunkEvent.response_data,
          protocol: chunkEvent.protocol,
        });
      }
      
      // Only send non-empty content
      if (extractedContent.trim()) {
        this.currentCallbacks?.onResponseChunk?.(extractedContent);
      }
      
    } catch (error) {
      console.warn('Failed to parse A2A chunk:', error);
      
      // Still try to send something to UI - show raw data
      const fallbackContent = this.extractFallbackContent(chunkEvent.response_data);
      if (fallbackContent) {
        this.currentCallbacks?.onResponseChunk?.(fallbackContent);
      }
    }
  }
  
  private extractFallbackContent(responseData: any): string {
    // Last resort: try to find any readable content
    if (typeof responseData === 'string') {
      return responseData;
    }
    
    if (responseData && typeof responseData === 'object') {
      // Look for common text fields
      const textFields = ['text', 'content', 'message', 'response'];
      
      for (const field of textFields) {
        if (responseData[field] && typeof responseData[field] === 'string') {
          return responseData[field];
        }
      }
    }
    
    // Give up and show stringified data
    try {
      return JSON.stringify(responseData, null, 2);
    } catch {
      return '[Unable to parse response]';
    }
  }
}
```

## 🧪 **Testing A2A Parser**

### **Unit Tests**

```typescript
// src/services/__tests__/a2aParser.test.ts

import { A2AParser } from '../a2aParser';

describe('A2AParser', () => {
  describe('extractContent', () => {
    it('should extract text from simple A2A response', () => {
      const response = {
        raw_response: {
          parts: [
            { kind: 'text', text: 'Hello ' },
            { kind: 'text', text: 'world!' }
          ]
        }
      };
      
      const result = A2AParser.extractContent(response);
      expect(result).toBe('Hello world!');
    });
    
    it('should handle parts without kind property', () => {
      const response = {
        raw_response: {
          parts: [
            { text: 'Hello from A2A agent' }
          ]
        }
      };
      
      const result = A2AParser.extractContent(response);
      expect(result).toBe('Hello from A2A agent');
    });
    
    it('should extract code content when no text parts', () => {
      const response = {
        raw_response: {
          parts: [
            {
              kind: 'code',
              code: {
                language: 'python',
                content: 'print("Hello, World!")'
              }
            }
          ]
        }
      };
      
      const result = A2AParser.extractContent(response);
      expect(result).toBe('```python\nprint("Hello, World!")\n```');
    });
    
    it('should handle malformed responses gracefully', () => {
      const badResponse = {
        raw_response: {
          parts: null
        }
      };
      
      const result = A2AParser.extractContent(badResponse);
      expect(result).toBe('No content available');
    });
    
    it('should validate response structure', () => {
      const validResponse = {
        raw_response: {
          parts: [{ kind: 'text', text: 'Valid' }]
        }
      };
      
      const invalidResponse = {
        raw_response: {
          parts: 'not an array'
        }
      };
      
      expect(A2AParser.validateResponse(validResponse)).toBe(true);
      expect(A2AParser.validateResponse(invalidResponse)).toBe(false);
    });
  });
  
  describe('parseStreamChunk', () => {
    it('should parse A2A streaming chunks', () => {
      const chunk = {
        event: 'response_chunk',
        protocol: 'a2a',
        response_data: {
          raw_response: {
            parts: [{ kind: 'text', text: 'Streaming text' }]
          }
        }
      };
      
      const result = A2AParser.parseStreamChunk(chunk);
      expect(result).toBe('Streaming text');
    });
    
    it('should reject non-A2A chunks', () => {
      const chunk = {
        protocol: 'acp',
        response_data: { content: 'ACP content' }
      };
      
      expect(() => A2AParser.parseStreamChunk(chunk)).toThrow('Invalid A2A stream chunk');
    });
  });
  
  describe('analyzeResponse', () => {
    it('should provide detailed analysis', () => {
      const response = {
        raw_response: {
          parts: [
            { kind: 'text', text: 'Hello' },
            { kind: 'code', code: { content: 'x = 1' } },
            { kind: 'text', text: ' world' }
          ]
        }
      };
      
      const analysis = A2AParser.analyzeResponse(response);
      
      expect(analysis.isValid).toBe(true);
      expect(analysis.partsCount).toBe(3);
      expect(analysis.textPartsCount).toBe(2);
      expect(analysis.partTypes).toContain('text');
      expect(analysis.partTypes).toContain('code');
      expect(analysis.totalTextLength).toBe(11); // "Hello" + " world"
      expect(analysis.errors).toHaveLength(0);
    });
  });
});
```

### **Integration Tests**

```typescript
// src/services/__tests__/a2aIntegration.test.ts

import { orchestratorApi } from '../orchestratorApi';
import { A2AParser } from '../a2aParser';

describe('A2A Integration', () => {
  const isRealApiTest = process.env.TEST_WITH_REAL_API === 'true';
  
  it.skipIf(!isRealApiTest)('should handle real A2A math agent response', async () => {
    const response = await orchestratorApi.processMessage('What is 5 + 3?');
    
    expect(response.protocol).toBe('a2a');
    expect(response.content).toContain('8');
    expect(response.agent_name).toContain('Math');
    
    // Validate the raw response structure
    expect(A2AParser.validateResponse(response.response_data)).toBe(true);
  });
  
  it.skipIf(!isRealApiTest)('should handle streaming A2A responses', async () => {
    const chunks: string[] = [];
    
    await streamingApi.processMessageStream('Calculate 10 * 7', {
      onResponseChunk: (chunk) => {
        chunks.push(chunk);
      },
      onCompleted: (data) => {
        expect(data.protocol).toBe('a2a');
      }
    });
    
    const fullResponse = chunks.join('');
    expect(fullResponse).toContain('70');
  }, 10000);
});
```

## 🛡️ **Error Handling Strategies**

### **Graceful Degradation**

```typescript
export class RobustA2AParser extends A2AParser {
  static extractContentWithFallback(responseData: any): {
    content: string;
    confidence: 'high' | 'medium' | 'low';
    warnings: string[];
  } {
    const warnings: string[] = [];
    
    try {
      // Try perfect parsing first
      const content = this.extractContent(responseData);
      return {
        content,
        confidence: 'high',
        warnings: []
      };
      
    } catch (primaryError) {
      warnings.push(`Primary parsing failed: ${primaryError.message}`);
      
      try {
        // Try fallback extraction
        const content = this.fallbackExtraction(responseData);
        return {
          content,
          confidence: 'medium',
          warnings
        };
        
      } catch (fallbackError) {
        warnings.push(`Fallback parsing failed: ${fallbackError.message}`);
        
        // Last resort - return raw data
        const content = JSON.stringify(responseData, null, 2);
        return {
          content: `Raw response data:\n\`\`\`json\n${content}\n\`\`\``,
          confidence: 'low',
          warnings
        };
      }
    }
  }
}
```

### **Performance Monitoring**

```typescript
export class InstrumentedA2AParser extends A2AParser {
  private static metrics = {
    parseAttempts: 0,
    parseSuccesses: 0,
    parseErrors: 0,
    averageParseTime: 0,
  };
  
  static extractContent(responseData: any): string {
    const startTime = performance.now();
    this.metrics.parseAttempts++;
    
    try {
      const result = super.extractContent(responseData);
      this.metrics.parseSuccesses++;
      
      const parseTime = performance.now() - startTime;
      this.updateAverageParseTime(parseTime);
      
      return result;
      
    } catch (error) {
      this.metrics.parseErrors++;
      throw error;
    }
  }
  
  private static updateAverageParseTime(newTime: number) {
    const { parseSuccesses, averageParseTime } = this.metrics;
    this.metrics.averageParseTime = 
      (averageParseTime * (parseSuccesses - 1) + newTime) / parseSuccesses;
  }
  
  static getMetrics() {
    return {
      ...this.metrics,
      successRate: this.metrics.parseSuccesses / this.metrics.parseAttempts,
    };
  }
}
```

## 🎯 **Key Takeaways**

1. **A2A uses "parts" arrays** - Always check for `raw_response.parts` structure
2. **Handle missing kind properties** - Some parts may omit the `kind` field
3. **Support multiple content types** - Text, code, images, tool calls all possible
4. **Validate before parsing** - A2A responses can be malformed
5. **Provide fallback extraction** - Always have a last resort for bad data
6. **Monitor parsing performance** - Track success rates and parse times
7. **Test with real agents** - Mock tests miss edge cases from real A2A agents

## 📋 **Next Steps**

In the next tutorial, we'll explore:
- **ACP Protocol Parsing**: Different structure and patterns
- **Protocol Detection**: Auto-detecting protocol from response format  
- **Unified Parser Interface**: Single API for all protocol types
- **Advanced Content Types**: Handling images, files, and rich media

---

**Next**: [02-acp-protocol-parsing.md](./02-acp-protocol-parsing.md) - ACP Protocol Implementation

**Previous**: [Phase 3: Streaming State Management](../phase-3-streaming/03-streaming-state-management.md)