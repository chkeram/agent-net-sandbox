# Protocol-Aware Parsing: ACP Protocol Implementation

## 🎯 **Learning Objectives**

By the end of this tutorial, you will:
- Understand the ACP (Agent Communication Protocol) structure and message formats
- Implement robust parsing for ACP regular and streaming responses
- Handle ACP-specific data structures and response patterns
- Build error-tolerant ACP parsing with comprehensive fallback strategies
- Create type-safe ACP integration with full TypeScript support

## 🔍 **ACP Protocol Overview**

The **ACP (Agent Communication Protocol)** is designed for standardized AI agent interactions with a focus on simplicity and direct content delivery. Our implementation integrates with the official ACP SDK.

### **Key Characteristics**
- **Direct Content**: Simpler, more direct content structure than A2A
- **JSON-RPC Based**: Built on JSON-RPC 2.0 standard
- **Streamlined**: Fewer nested structures, easier parsing
- **Performance Focused**: Optimized for low-latency communication

### **ACP Request Structure**
```json
{
  "jsonrpc": "2.0",
  "method": "process",
  "params": {
    "query": "Hello, how are you?"
  },
  "id": "req_456"
}
```

## 📦 **ACP Response Formats**

### **Regular API Response**
```json
{
  "request_id": "req_456",
  "agent_id": "acp-hello-world",
  "agent_name": "ACP Hello World Agent", 
  "protocol": "acp",
  "response_data": {
    "content": "Hello! I'm doing well, thank you for asking.",
    "metadata": {
      "processing_time": 0.123,
      "model": "gpt-4"
    }
  },
  "confidence": 0.98,
  "reasoning": "Greeting detected - routing to hello world agent",
  "success": true
}
```

### **Alternative ACP Response Formats**
```json
// Format 1: Direct content field
{
  "response_data": {
    "content": "Direct response text"
  }
}

// Format 2: Response field
{
  "response_data": {
    "response": "Response in response field"
  }
}

// Format 3: Output field (tool/function results)
{
  "response_data": {
    "output": "Function execution result"
  }
}

// Format 4: Nested data structure
{
  "response_data": {
    "data": {
      "message": "Nested message content"
    }
  }
}
```

### **ACP Streaming Chunks**
```json
{
  "event": "response_chunk",
  "protocol": "acp",
  "response_data": {
    "content": "Streaming ",
    "chunk_id": 1
  }
}
```

## 🛠️ **ACP Parser Implementation**

### **Step 1: Type Definitions**

```typescript
// src/types/acp.ts

export interface ACPMetadata {
  processing_time?: number;
  model?: string;
  temperature?: number;
  tokens_used?: number;
  [key: string]: any;
}

export interface ACPResponseData {
  content?: string;
  response?: string;
  output?: string;
  message?: string;
  text?: string;
  data?: {
    message?: string;
    content?: string;
    text?: string;
    [key: string]: any;
  };
  metadata?: ACPMetadata;
  [key: string]: any;
}

export interface ACPResponse {
  jsonrpc?: "2.0";
  result?: ACPResponseData;
  id?: string;
  // For direct orchestrator responses
  response_data?: ACPResponseData;
}

export interface ACPStreamChunk {
  event: 'response_chunk';
  protocol: 'acp';
  response_data: ACPResponseData;
  chunk_id?: number;
}
```

### **Step 2: Core ACP Parser Class**

```typescript
// src/services/acpParser.ts

export class ACPParser {
  /**
   * Extract clean text content from ACP response data
   */
  static extractContent(responseData: any): string {
    try {
      if (!responseData) {
        throw new Error('No response data provided');
      }
      
      // Try multiple content extraction strategies
      const extractors = [
        this.extractFromContentField,
        this.extractFromResponseField,
        this.extractFromOutputField,
        this.extractFromDataNested,
        this.extractFromAnyTextField,
        this.extractFromMetadata,
      ];
      
      for (const extractor of extractors) {
        try {
          const result = extractor(responseData);
          if (result && result.trim().length > 0) {
            return result.trim();
          }
        } catch (extractorError) {
          // Continue to next extractor
          console.debug(`ACP extractor failed:`, extractorError.message);
        }
      }
      
      // If no extractors worked, try fallback
      return this.fallbackExtraction(responseData);
      
    } catch (error) {
      console.warn('ACP parsing failed:', error);
      return this.emergencyFallback(responseData);
    }
  }
  
  /**
   * Strategy 1: Extract from direct content field
   */
  private static extractFromContentField(responseData: any): string {
    if (responseData.content && typeof responseData.content === 'string') {
      return responseData.content;
    }
    throw new Error('No content field found');
  }
  
  /**
   * Strategy 2: Extract from response field  
   */
  private static extractFromResponseField(responseData: any): string {
    if (responseData.response && typeof responseData.response === 'string') {
      return responseData.response;
    }
    throw new Error('No response field found');
  }
  
  /**
   * Strategy 3: Extract from output field (function/tool results)
   */
  private static extractFromOutputField(responseData: any): string {
    if (responseData.output) {
      if (typeof responseData.output === 'string') {
        return responseData.output;
      }
      // Handle structured output
      if (typeof responseData.output === 'object') {
        const result = responseData.output.result || 
                      responseData.output.content ||
                      responseData.output.message;
        if (result && typeof result === 'string') {
          return result;
        }
      }
    }
    throw new Error('No output field found');
  }
  
  /**
   * Strategy 4: Extract from nested data structure
   */
  private static extractFromDataNested(responseData: any): string {
    if (responseData.data && typeof responseData.data === 'object') {
      const nested = responseData.data;
      
      // Try common nested field names
      const fields = ['message', 'content', 'text', 'response'];
      for (const field of fields) {
        if (nested[field] && typeof nested[field] === 'string') {
          return nested[field];
        }
      }
    }
    throw new Error('No nested data found');
  }
  
  /**
   * Strategy 5: Search for any text field recursively
   */
  private static extractFromAnyTextField(responseData: any): string {
    const textFields = ['text', 'message', 'msg', 'body', 'answer'];
    
    for (const field of textFields) {
      if (responseData[field] && typeof responseData[field] === 'string') {
        return responseData[field];
      }
    }
    
    throw new Error('No recognizable text fields found');
  }
  
  /**
   * Strategy 6: Extract from metadata if available
   */
  private static extractFromMetadata(responseData: any): string {
    if (responseData.metadata) {
      const meta = responseData.metadata;
      if (meta.summary && typeof meta.summary === 'string') {
        return meta.summary;
      }
      if (meta.description && typeof meta.description === 'string') {
        return meta.description;
      }
    }
    throw new Error('No metadata content found');
  }
  
  /**
   * Fallback extraction for unknown structures
   */
  private static fallbackExtraction(responseData: any): string {
    // Deep search for any string values that could be content
    const findStrings = (obj: any, path = ''): Array<{value: string, path: string}> => {
      const results: Array<{value: string, path: string}> = [];
      
      if (typeof obj === 'string' && obj.trim().length > 0) {
        results.push({ value: obj.trim(), path });
      } else if (obj && typeof obj === 'object') {
        for (const [key, value] of Object.entries(obj)) {
          const currentPath = path ? `${path}.${key}` : key;
          results.push(...findStrings(value, currentPath));
        }
      }
      
      return results;
    };
    
    const foundStrings = findStrings(responseData);
    
    // Filter out likely non-content strings
    const contentStrings = foundStrings.filter(({ value, path }) => {
      // Skip very short strings
      if (value.length < 3) return false;
      
      // Skip technical fields
      const technicalPaths = ['id', 'timestamp', 'version', 'type', 'status', 'code'];
      if (technicalPaths.some(tech => path.toLowerCase().includes(tech))) {
        return false;
      }
      
      // Skip UUID-like strings
      if (/^[a-f0-9\-]{20,}$/i.test(value)) return false;
      
      return true;
    });
    
    if (contentStrings.length > 0) {
      // Return the longest string found (most likely to be content)
      const longest = contentStrings.reduce((prev, current) => 
        current.value.length > prev.value.length ? current : prev
      );
      return longest.value;
    }
    
    throw new Error('No content found in fallback extraction');
  }
  
  /**
   * Emergency fallback when all else fails
   */
  private static emergencyFallback(responseData: any): string {
    if (typeof responseData === 'string') {
      return responseData;
    }
    
    try {
      // Last resort: show structured data to user
      return `ACP Response Data:\n\`\`\`json\n${JSON.stringify(responseData, null, 2)}\n\`\`\``;
    } catch {
      return 'Unable to parse ACP response';
    }
  }
  
  /**
   * Parse streaming chunk specifically
   */
  static parseStreamChunk(chunkData: any): string {
    if (!chunkData || chunkData.protocol !== 'acp') {
      throw new Error('Invalid ACP stream chunk');
    }
    
    return this.extractContent(chunkData.response_data);
  }
  
  /**
   * Validate ACP response structure
   */
  static validateResponse(responseData: any): boolean {
    if (!responseData) {
      return false;
    }
    
    // ACP is valid if we can extract any content
    try {
      const content = this.extractContent(responseData);
      return content.length > 0;
    } catch {
      return false;
    }
  }
  
  /**
   * Get detailed analysis of ACP response
   */
  static analyzeResponse(responseData: any): {
    isValid: boolean;
    contentFound: boolean;
    extractionMethod: string | null;
    contentLength: number;
    availableFields: string[];
    errors: string[];
  } {
    const analysis = {
      isValid: false,
      contentFound: false,
      extractionMethod: null as string | null,
      contentLength: 0,
      availableFields: [] as string[],
      errors: [] as string[],
    };
    
    try {
      if (!responseData) {
        analysis.errors.push('No response data provided');
        return analysis;
      }
      
      // Collect available fields
      if (typeof responseData === 'object') {
        analysis.availableFields = Object.keys(responseData);
      }
      
      // Test each extraction method
      const methods = [
        { name: 'content', method: this.extractFromContentField },
        { name: 'response', method: this.extractFromResponseField },
        { name: 'output', method: this.extractFromOutputField },
        { name: 'nested', method: this.extractFromDataNested },
        { name: 'textField', method: this.extractFromAnyTextField },
        { name: 'metadata', method: this.extractFromMetadata },
      ];
      
      for (const { name, method } of methods) {
        try {
          const content = method(responseData);
          if (content && content.trim().length > 0) {
            analysis.isValid = true;
            analysis.contentFound = true;
            analysis.extractionMethod = name;
            analysis.contentLength = content.trim().length;
            break;
          }
        } catch (error) {
          // Method failed, continue to next
        }
      }
      
      // If no specific method worked, try fallback
      if (!analysis.contentFound) {
        try {
          const content = this.fallbackExtraction(responseData);
          analysis.isValid = true;
          analysis.contentFound = true;
          analysis.extractionMethod = 'fallback';
          analysis.contentLength = content.length;
        } catch (error) {
          analysis.errors.push(`Fallback failed: ${error.message}`);
        }
      }
      
    } catch (error) {
      analysis.errors.push(`Analysis failed: ${error.message}`);
    }
    
    return analysis;
  }
  
  /**
   * Extract metadata from ACP response
   */
  static extractMetadata(responseData: any): ACPMetadata | null {
    try {
      if (responseData?.metadata && typeof responseData.metadata === 'object') {
        return responseData.metadata;
      }
      return null;
    } catch {
      return null;
    }
  }
}
```

### **Step 3: Integration with Orchestrator API**

```typescript
// src/services/orchestratorApi.ts (ACP-specific additions)

import { ACPParser } from './acpParser';

class OrchestratorAPI {
  // ... existing methods ...
  
  /**
   * Enhanced content extraction with ACP support
   */
  public extractResponseContent(data: any): string {
    const protocol = data.protocol?.toLowerCase();
    
    // Use specialized ACP parser
    if (protocol === 'acp') {
      return ACPParser.extractContent(data.response_data);
    }
    
    // Handle A2A and other protocols...
    return this.genericContentExtraction(data);
  }
  
  /**
   * Extract metadata for ACP responses
   */
  public extractResponseMetadata(data: any): any {
    const protocol = data.protocol?.toLowerCase();
    
    if (protocol === 'acp') {
      return ACPParser.extractMetadata(data.response_data);
    }
    
    return null;
  }
  
  /**
   * Enhanced process response with ACP metadata
   */
  private parseProcessResponse(rawResponse: any): ProcessResponse {
    const content = this.extractResponseContent(rawResponse);
    const metadata = this.extractResponseMetadata(rawResponse);
    
    return {
      request_id: rawResponse.request_id || 'unknown',
      agent_id: rawResponse.agent_id || 'unknown',
      agent_name: rawResponse.agent_name || 'Unknown Agent',
      protocol: rawResponse.protocol || 'unknown',
      content,
      confidence: rawResponse.confidence || 0,
      reasoning: rawResponse.reasoning,
      response_data: rawResponse.response_data,
      metadata, // Include parsed metadata
      success: rawResponse.success ?? true,
      duration_ms: rawResponse.duration_ms || 0,
      timestamp: rawResponse.timestamp || new Date().toISOString(),
    };
  }
}
```

### **Step 4: Streaming Integration**

```typescript
// src/services/streamingApi.ts (ACP streaming support)

import { ACPParser } from './acpParser';

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
      if (chunkEvent.protocol.toLowerCase() === 'acp') {
        extractedContent = ACPParser.parseStreamChunk(chunkEvent);
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
      console.warn('Failed to parse ACP chunk:', error);
      
      // Provide detailed error info for ACP
      if (chunkEvent.protocol.toLowerCase() === 'acp') {
        const analysis = ACPParser.analyzeResponse(chunkEvent.response_data);
        console.debug('ACP chunk analysis:', analysis);
        
        // Try to show available fields to user
        const availableInfo = `Available fields: ${analysis.availableFields.join(', ')}`;
        this.currentCallbacks?.onResponseChunk?.(`[Parsing Error: ${availableInfo}]`);
      } else {
        // Generic fallback for other protocols
        const fallbackContent = this.extractFallbackContent(chunkEvent.response_data);
        if (fallbackContent) {
          this.currentCallbacks?.onResponseChunk?.(fallbackContent);
        }
      }
    }
  }
}
```

## 🧪 **Testing ACP Parser**

### **Unit Tests**

```typescript
// src/services/__tests__/acpParser.test.ts

import { ACPParser } from '../acpParser';

describe('ACPParser', () => {
  describe('extractContent', () => {
    it('should extract from content field', () => {
      const response = {
        content: 'Hello from ACP agent!'
      };
      
      const result = ACPParser.extractContent(response);
      expect(result).toBe('Hello from ACP agent!');
    });
    
    it('should extract from response field', () => {
      const response = {
        response: 'Response field content'
      };
      
      const result = ACPParser.extractContent(response);
      expect(result).toBe('Response field content');
    });
    
    it('should extract from output field', () => {
      const response = {
        output: 'Function execution result'
      };
      
      const result = ACPParser.extractContent(response);
      expect(result).toBe('Function execution result');
    });
    
    it('should extract from nested data structure', () => {
      const response = {
        data: {
          message: 'Nested message content'
        }
      };
      
      const result = ACPParser.extractContent(response);
      expect(result).toBe('Nested message content');
    });
    
    it('should handle structured output', () => {
      const response = {
        output: {
          result: 'Structured result',
          metadata: { type: 'calculation' }
        }
      };
      
      const result = ACPParser.extractContent(response);
      expect(result).toBe('Structured result');
    });
    
    it('should fallback to deep string search', () => {
      const response = {
        someField: {
          nested: {
            deepContent: 'Found deep content'
          }
        }
      };
      
      const result = ACPParser.extractContent(response);
      expect(result).toBe('Found deep content');
    });
    
    it('should handle empty responses gracefully', () => {
      const response = {};
      
      const result = ACPParser.extractContent(response);
      expect(result).toContain('ACP Response Data');
    });
    
    it('should validate response structure', () => {
      const validResponse = { content: 'Valid content' };
      const invalidResponse = {};
      
      expect(ACPParser.validateResponse(validResponse)).toBe(true);
      expect(ACPParser.validateResponse(invalidResponse)).toBe(false);
    });
  });
  
  describe('parseStreamChunk', () => {
    it('should parse ACP streaming chunks', () => {
      const chunk = {
        event: 'response_chunk',
        protocol: 'acp',
        response_data: {
          content: 'Streaming content'
        }
      };
      
      const result = ACPParser.parseStreamChunk(chunk);
      expect(result).toBe('Streaming content');
    });
    
    it('should reject non-ACP chunks', () => {
      const chunk = {
        protocol: 'a2a',
        response_data: { content: 'A2A content' }
      };
      
      expect(() => ACPParser.parseStreamChunk(chunk)).toThrow('Invalid ACP stream chunk');
    });
  });
  
  describe('analyzeResponse', () => {
    it('should provide detailed analysis', () => {
      const response = {
        content: 'Test content',
        metadata: {
          processing_time: 0.123,
          model: 'gpt-4'
        }
      };
      
      const analysis = ACPParser.analyzeResponse(response);
      
      expect(analysis.isValid).toBe(true);
      expect(analysis.contentFound).toBe(true);
      expect(analysis.extractionMethod).toBe('content');
      expect(analysis.contentLength).toBe(12); // "Test content"
      expect(analysis.availableFields).toContain('content');
      expect(analysis.availableFields).toContain('metadata');
      expect(analysis.errors).toHaveLength(0);
    });
    
    it('should handle failed parsing', () => {
      const response = null;
      
      const analysis = ACPParser.analyzeResponse(response);
      
      expect(analysis.isValid).toBe(false);
      expect(analysis.contentFound).toBe(false);
      expect(analysis.extractionMethod).toBeNull();
      expect(analysis.errors.length).toBeGreaterThan(0);
    });
  });
  
  describe('extractMetadata', () => {
    it('should extract metadata when present', () => {
      const response = {
        content: 'Test',
        metadata: {
          processing_time: 0.456,
          model: 'gpt-4',
          tokens_used: 150
        }
      };
      
      const metadata = ACPParser.extractMetadata(response);
      
      expect(metadata).toEqual({
        processing_time: 0.456,
        model: 'gpt-4',
        tokens_used: 150
      });
    });
    
    it('should return null when no metadata', () => {
      const response = { content: 'Test' };
      
      const metadata = ACPParser.extractMetadata(response);
      
      expect(metadata).toBeNull();
    });
  });
});
```

### **Integration Tests**

```typescript
// src/services/__tests__/acpIntegration.test.ts

import { orchestratorApi } from '../orchestratorApi';
import { ACPParser } from '../acpParser';

describe('ACP Integration', () => {
  const isRealApiTest = process.env.TEST_WITH_REAL_API === 'true';
  
  it.skipIf(!isRealApiTest)('should handle real ACP hello world agent response', async () => {
    const response = await orchestratorApi.processMessage('Hello there!');
    
    expect(response.protocol).toBe('acp');
    expect(response.content).toContain('hello');
    expect(response.agent_name).toContain('Hello');
    
    // Validate the response structure
    expect(ACPParser.validateResponse(response.response_data)).toBe(true);
  });
  
  it.skipIf(!isRealApiTest)('should handle streaming ACP responses', async () => {
    const chunks: string[] = [];
    
    await streamingApi.processMessageStream('Say hello to me', {
      onResponseChunk: (chunk) => {
        chunks.push(chunk);
      },
      onCompleted: (data) => {
        expect(data.protocol).toBe('acp');
      }
    });
    
    const fullResponse = chunks.join('');
    expect(fullResponse.toLowerCase()).toContain('hello');
  }, 10000);
  
  it.skipIf(!isRealApiTest)('should extract metadata from real responses', async () => {
    const response = await orchestratorApi.processMessage('Hello!');
    
    if (response.protocol === 'acp' && response.metadata) {
      expect(typeof response.metadata).toBe('object');
      // Metadata might contain processing_time, model, etc.
    }
  });
});
```

## 🛡️ **Advanced ACP Error Handling**

### **Robust Content Extraction**

```typescript
export class RobustACPParser extends ACPParser {
  static extractContentWithMetrics(responseData: any): {
    content: string;
    extractionMethod: string;
    confidence: 'high' | 'medium' | 'low';
    processingTime: number;
    warnings: string[];
  } {
    const startTime = performance.now();
    const warnings: string[] = [];
    
    try {
      const analysis = this.analyzeResponse(responseData);
      
      if (!analysis.isValid) {
        warnings.push('Response validation failed');
        warnings.push(...analysis.errors);
      }
      
      const content = this.extractContent(responseData);
      
      return {
        content,
        extractionMethod: analysis.extractionMethod || 'unknown',
        confidence: this.determineConfidence(analysis),
        processingTime: performance.now() - startTime,
        warnings
      };
      
    } catch (error) {
      warnings.push(`Extraction failed: ${error.message}`);
      
      return {
        content: `Error: ${error.message}`,
        extractionMethod: 'error',
        confidence: 'low',
        processingTime: performance.now() - startTime,
        warnings
      };
    }
  }
  
  private static determineConfidence(analysis: any): 'high' | 'medium' | 'low' {
    if (!analysis.contentFound) return 'low';
    
    // High confidence for direct content fields
    if (['content', 'response', 'output'].includes(analysis.extractionMethod)) {
      return 'high';
    }
    
    // Medium confidence for structured extraction
    if (['nested', 'textField'].includes(analysis.extractionMethod)) {
      return 'medium';
    }
    
    // Low confidence for fallback methods
    return 'low';
  }
}
```

### **Content Quality Assessment**

```typescript
export class ACPContentValidator {
  static assessContentQuality(content: string): {
    isValid: boolean;
    quality: 'high' | 'medium' | 'low';
    issues: string[];
    suggestions: string[];
  } {
    const issues: string[] = [];
    const suggestions: string[] = [];
    
    // Check basic validity
    if (!content || content.trim().length === 0) {
      issues.push('Empty content');
      suggestions.push('Check if agent is returning responses');
      return { isValid: false, quality: 'low', issues, suggestions };
    }
    
    // Check for technical artifacts
    if (content.includes('undefined') || content.includes('null')) {
      issues.push('Contains undefined/null values');
      suggestions.push('Agent may have data processing issues');
    }
    
    // Check for JSON artifacts
    if (content.startsWith('{') && content.endsWith('}')) {
      try {
        JSON.parse(content);
        issues.push('Content appears to be raw JSON');
        suggestions.push('Parser may not be extracting content properly');
      } catch {
        // Not valid JSON, which is fine
      }
    }
    
    // Check content length
    if (content.length < 5) {
      issues.push('Very short content');
      suggestions.push('Agent may not be processing queries properly');
    } else if (content.length > 10000) {
      issues.push('Extremely long content');
      suggestions.push('Consider implementing content truncation');
    }
    
    // Determine quality
    let quality: 'high' | 'medium' | 'low';
    if (issues.length === 0) {
      quality = 'high';
    } else if (issues.length <= 2) {
      quality = 'medium';
    } else {
      quality = 'low';
    }
    
    return {
      isValid: content.trim().length > 0,
      quality,
      issues,
      suggestions
    };
  }
}
```

## 🔧 **Performance Optimization**

### **Caching Parser Results**

```typescript
export class CachedACPParser extends ACPParser {
  private static cache = new Map<string, { content: string; timestamp: number }>();
  private static CACHE_TTL = 5000; // 5 seconds
  
  static extractContent(responseData: any): string {
    // Create cache key from response data
    const cacheKey = this.createCacheKey(responseData);
    const cached = this.cache.get(cacheKey);
    
    if (cached && Date.now() - cached.timestamp < this.CACHE_TTL) {
      return cached.content;
    }
    
    // Extract content normally
    const content = super.extractContent(responseData);
    
    // Cache result
    this.cache.set(cacheKey, {
      content,
      timestamp: Date.now()
    });
    
    // Clean old cache entries
    this.cleanCache();
    
    return content;
  }
  
  private static createCacheKey(responseData: any): string {
    try {
      return JSON.stringify(responseData);
    } catch {
      return String(responseData);
    }
  }
  
  private static cleanCache(): void {
    const now = Date.now();
    for (const [key, value] of this.cache.entries()) {
      if (now - value.timestamp >= this.CACHE_TTL) {
        this.cache.delete(key);
      }
    }
  }
}
```

## 🎯 **Key Takeaways**

1. **ACP is simpler than A2A** - Direct content fields, fewer nested structures
2. **Multiple content field names** - `content`, `response`, `output` all possible
3. **Flexible structure support** - Handle various ACP implementations
4. **Fallback extraction crucial** - ACP agents vary in response format
5. **Metadata is valuable** - ACP often includes useful processing metadata
6. **Quality assessment important** - Validate extracted content makes sense
7. **Caching improves performance** - Especially for repeated requests

## 📋 **Next Steps**

In the next tutorial, we'll explore:
- **Unified Protocol Parser**: Single interface for all protocols
- **Auto-Detection**: Automatically identify protocol from response structure
- **Custom Protocol Support**: Adding new protocols to the system
- **Protocol Migration**: Handling agents that switch protocols

---

**Next**: [03-unified-protocol-parser.md](./03-unified-protocol-parser.md) - Unified Multi-Protocol Parser

**Previous**: [01-a2a-protocol-parsing.md](./01-a2a-protocol-parsing.md)