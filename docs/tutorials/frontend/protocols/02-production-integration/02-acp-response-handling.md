# Protocol-Aware Parsing: ACP Response Handling

## 🎯 **Learning Objectives**

By the end of this tutorial, you will:
- Understand the ACP (Agent Communication Protocol) response structure
- Build parsers for ACP message formats and capabilities
- Handle ACP-specific features like tool calls and function responses
- Implement unified parsing that works with both A2A and ACP protocols
- Create robust error handling for protocol-agnostic applications

## 🌐 **What is the ACP Protocol?**

The **Agent Communication Protocol (ACP)** is a standardized protocol for AI agent communication that emphasizes:

- **Tool Integration**: Agents can call external tools and functions
- **Structured Responses**: Clear separation between content and metadata
- **Capability Discovery**: Agents expose their available tools and capabilities
- **State Management**: Support for conversation context and state persistence

### **ACP vs A2A Comparison**

| Feature | ACP | A2A |
|---------|-----|-----|
| **Message Structure** | Simple content + metadata | Structured parts |
| **Tool Support** | Built-in tool calling | Extension-based |
| **Content Types** | Text-focused with attachments | Rich media parts |
| **Complexity** | Lower | Higher |
| **Use Cases** | Task automation, workflows | Rich content, multimedia |

## 📋 **ACP Response Structure**

### **Basic ACP Agent Response**

```json
{
  "content": "Hello! I'm ready to help with mathematical calculations.",
  "metadata": {
    "agent_id": "acp-hello-world",
    "agent_name": "Hello World Agent",
    "version": "1.0.0",
    "timestamp": "2024-01-15T10:30:00Z",
    "response_type": "greeting"
  },
  "capabilities": [
    {
      "name": "greet",
      "description": "Provide friendly greetings",
      "parameters": {
        "name": {"type": "string", "optional": true}
      }
    }
  ],
  "tools": [],
  "status": "ready"
}
```

### **ACP Tool Call Response**

```json
{
  "content": "I'll help you calculate that. Let me use the math tool.",
  "tool_calls": [
    {
      "id": "call_123",
      "tool": "calculator",
      "function": "multiply",
      "parameters": {
        "a": 15,
        "b": 23
      }
    }
  ],
  "metadata": {
    "agent_id": "acp-calculator",
    "thinking": "User wants to multiply 15 by 23, I'll use the calculator tool"
  }
}
```

### **Orchestrator-Wrapped ACP Response**

```json
{
  "request_id": "req_456",
  "agent_id": "acp-hello-world",
  "agent_name": "Hello World Agent",
  "protocol": "acp",
  "confidence": 0.88,
  "reasoning": "Simple greeting - Hello World Agent is perfect for this",
  "response_data": {
    "content": "Hello there! How can I assist you today?",
    "metadata": {
      "agent_id": "acp-hello-world",
      "response_type": "greeting"
    },
    "capabilities": [
      {
        "name": "greet",
        "description": "Provide friendly greetings"
      }
    ]
  },
  "success": true,
  "duration_ms": 89,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🛠️ **Building ACP Response Parser**

### **Step 1: ACP Type Definitions**

```typescript
// src/types/acp.ts

// Tool parameter definition
export interface ACPParameter {
  type: 'string' | 'number' | 'boolean' | 'object' | 'array';
  description?: string;
  optional?: boolean;
  enum?: any[];
  default?: any;
}

// Tool/capability definition
export interface ACPCapability {
  name: string;
  description: string;
  parameters?: Record<string, ACPParameter>;
  returns?: ACPParameter;
  examples?: Array<{
    input: Record<string, any>;
    output: any;
    description?: string;
  }>;
}

// Tool call (when agent wants to use a tool)
export interface ACPToolCall {
  id: string;
  tool: string;
  function: string;
  parameters: Record<string, any>;
}

// Tool result (response from tool execution)
export interface ACPToolResult {
  id: string;
  result: any;
  error?: string;
  execution_time?: number;
}

// ACP message metadata
export interface ACPMetadata {
  agent_id: string;
  agent_name?: string;
  version?: string;
  timestamp?: string;
  response_type?: string;
  thinking?: string; // Agent's reasoning process
  confidence?: number;
  [key: string]: any; // Allow additional metadata
}

// Core ACP response structure
export interface ACPResponse {
  content: string;
  metadata?: ACPMetadata;
  capabilities?: ACPCapability[];
  tools?: ACPCapability[]; // Available tools
  tool_calls?: ACPToolCall[]; // Tools the agent wants to call
  tool_results?: ACPToolResult[]; // Results from tool execution
  attachments?: Array<{
    type: 'file' | 'image' | 'link';
    url?: string;
    data?: string;
    filename?: string;
    mimetype?: string;
  }>;
  status?: 'ready' | 'thinking' | 'working' | 'done' | 'error';
  error?: {
    code: string;
    message: string;
    details?: any;
  };
}

// Parsed ACP content for UI display
export interface ParsedACPContent {
  textContent: string;
  toolCalls: Array<{
    id: string;
    tool: string;
    function: string;
    parameters: Record<string, any>;
  }>;
  toolResults: Array<{
    id: string;
    result: any;
    error?: string;
  }>;
  attachments: Array<{
    type: string;
    url?: string;
    filename?: string;
    data?: string;
  }>;
  capabilities: ACPCapability[];
  metadata: ACPMetadata;
  status: string;
  thinking?: string;
}
```

### **Step 2: ACP Parser Implementation**

```typescript
// src/services/acpParser.ts
import type { 
  ACPResponse, 
  ParsedACPContent,
  ACPCapability,
  ACPMetadata,
  ACPToolCall,
  ACPToolResult
} from '../types/acp';

export class ACPResponseParser {
  /**
   * Parse orchestrator response containing ACP data
   */
  static parseOrchestratorResponse(orchestratorResponse: any): ParsedACPContent | null {
    try {
      const responseData = orchestratorResponse.response_data;
      if (!responseData) {
        console.warn('No response_data in orchestrator response');
        return null;
      }

      // ACP responses can be structured in different ways
      let acpResponse: ACPResponse;

      if (typeof responseData === 'string') {
        // Simple text response
        acpResponse = {
          content: responseData,
          metadata: {
            agent_id: orchestratorResponse.agent_id || 'unknown',
            agent_name: orchestratorResponse.agent_name,
          },
        };
      } else if (responseData.content !== undefined) {
        // Structured ACP response
        acpResponse = responseData as ACPResponse;
      } else {
        // Try to extract content from various possible fields
        const content = responseData.response || 
                       responseData.output || 
                       responseData.text || 
                       responseData.message || 
                       'No content available';
        
        acpResponse = {
          content: typeof content === 'string' ? content : JSON.stringify(content),
          metadata: responseData.metadata || {
            agent_id: orchestratorResponse.agent_id || 'unknown',
          },
        };
      }

      return this.parseACPResponse(acpResponse);
    } catch (error) {
      console.error('Failed to parse orchestrator ACP response:', error);
      return null;
    }
  }

  /**
   * Parse raw ACP response
   */
  static parseACPResponse(response: ACPResponse): ParsedACPContent {
    try {
      const parsed: ParsedACPContent = {
        textContent: response.content || '',
        toolCalls: [],
        toolResults: [],
        attachments: [],
        capabilities: [],
        metadata: response.metadata || { agent_id: 'unknown' },
        status: response.status || 'ready',
        thinking: response.metadata?.thinking,
      };

      // Process tool calls
      if (response.tool_calls && Array.isArray(response.tool_calls)) {
        parsed.toolCalls = response.tool_calls.map(this.processToolCall);
      }

      // Process tool results
      if (response.tool_results && Array.isArray(response.tool_results)) {
        parsed.toolResults = response.tool_results.map(this.processToolResult);
      }

      // Process attachments
      if (response.attachments && Array.isArray(response.attachments)) {
        parsed.attachments = response.attachments.map(attachment => ({
          type: attachment.type,
          url: attachment.url,
          filename: attachment.filename,
          data: attachment.data,
        }));
      }

      // Process capabilities (combine capabilities and tools)
      const allCapabilities = [
        ...(response.capabilities || []),
        ...(response.tools || []),
      ];
      parsed.capabilities = allCapabilities.map(this.processCapability);

      return parsed;
    } catch (error) {
      console.error('Failed to parse ACP response:', error);
      
      // Return minimal parsed content on error
      return {
        textContent: response.content || 'Parse error occurred',
        toolCalls: [],
        toolResults: [],
        attachments: [],
        capabilities: [],
        metadata: response.metadata || { agent_id: 'unknown' },
        status: 'error',
      };
    }
  }

  /**
   * Process individual tool call
   */
  private static processToolCall(toolCall: ACPToolCall): ParsedACPContent['toolCalls'][0] {
    return {
      id: toolCall.id,
      tool: toolCall.tool,
      function: toolCall.function,
      parameters: toolCall.parameters || {},
    };
  }

  /**
   * Process individual tool result
   */
  private static processToolResult(toolResult: ACPToolResult): ParsedACPContent['toolResults'][0] {
    return {
      id: toolResult.id,
      result: toolResult.result,
      error: toolResult.error,
    };
  }

  /**
   * Process capability definition
   */
  private static processCapability(capability: ACPCapability): ACPCapability {
    return {
      name: capability.name,
      description: capability.description,
      parameters: capability.parameters,
      returns: capability.returns,
      examples: capability.examples,
    };
  }

  /**
   * Extract simple text content for basic use cases
   */
  static extractSimpleContent(orchestratorResponse: any): string {
    const parsed = this.parseOrchestratorResponse(orchestratorResponse);
    
    if (!parsed) {
      return 'Unable to parse ACP response';
    }

    let content = parsed.textContent;

    // Add tool call information if present
    if (parsed.toolCalls.length > 0) {
      const toolInfo = parsed.toolCalls.map(call => 
        `🔧 Using ${call.tool}.${call.function}(${JSON.stringify(call.parameters)})`
      ).join('\n');
      content += `\n\n${toolInfo}`;
    }

    // Add tool results if present
    if (parsed.toolResults.length > 0) {
      const resultInfo = parsed.toolResults.map(result => 
        `📊 Result: ${typeof result.result === 'object' 
          ? JSON.stringify(result.result) 
          : result.result}`
      ).join('\n');
      content += `\n\n${resultInfo}`;
    }

    // Add thinking process if available
    if (parsed.thinking && !content.includes(parsed.thinking)) {
      content += `\n\n*Agent thinking: ${parsed.thinking}*`;
    }

    return content.trim() || 'No content available';
  }
}
```

### **Step 3: Unified Protocol Parser**

```typescript
// src/services/protocolParser.ts
import { A2AResponseParser } from './a2aParser';
import { ACPResponseParser } from './acpParser';

export type ProtocolType = 'a2a' | 'acp' | 'mcp' | 'unknown';

export interface UnifiedParsedContent {
  textContent: string;
  protocol: ProtocolType;
  
  // A2A-specific content
  a2aContent?: import('./a2aParser').ParsedA2AContent;
  
  // ACP-specific content
  acpContent?: import('./acpParser').ParsedACPContent;
  
  // Common metadata
  agentInfo: {
    id: string;
    name: string;
    protocol: string;
  };
  
  // Error information
  errors: string[];
}

export class UnifiedProtocolParser {
  /**
   * Parse any orchestrator response regardless of protocol
   */
  static parseResponse(orchestratorResponse: any): UnifiedParsedContent {
    const protocol = this.detectProtocol(orchestratorResponse);
    const errors: string[] = [];
    
    let textContent = '';
    let a2aContent: import('./a2aParser').ParsedA2AContent | undefined;
    let acpContent: import('./acpParser').ParsedACPContent | undefined;

    try {
      switch (protocol) {
        case 'a2a':
          a2aContent = A2AResponseParser.parseOrchestratorResponse(orchestratorResponse);
          textContent = a2aContent?.textContent || '';
          break;
          
        case 'acp':
          acpContent = ACPResponseParser.parseOrchestratorResponse(orchestratorResponse);
          textContent = acpContent?.textContent || '';
          break;
          
        default:
          // Generic fallback parsing
          textContent = this.extractGenericContent(orchestratorResponse);
          errors.push(`Unknown protocol: ${protocol}`);
      }
    } catch (error) {
      errors.push(`Protocol parsing failed: ${error.message}`);
      textContent = this.extractGenericContent(orchestratorResponse);
    }

    return {
      textContent: textContent || 'No content available',
      protocol,
      a2aContent,
      acpContent,
      agentInfo: {
        id: orchestratorResponse.agent_id || 'unknown',
        name: orchestratorResponse.agent_name || 'Unknown Agent',
        protocol: orchestratorResponse.protocol || protocol,
      },
      errors,
    };
  }

  /**
   * Detect protocol from orchestrator response
   */
  private static detectProtocol(orchestratorResponse: any): ProtocolType {
    // Check explicit protocol field
    const explicitProtocol = orchestratorResponse.protocol?.toLowerCase();
    if (explicitProtocol === 'a2a' || explicitProtocol === 'acp' || explicitProtocol === 'mcp') {
      return explicitProtocol;
    }

    // Detect by agent ID pattern
    const agentId = orchestratorResponse.agent_id?.toLowerCase() || '';
    if (agentId.includes('a2a')) return 'a2a';
    if (agentId.includes('acp')) return 'acp';
    if (agentId.includes('mcp')) return 'mcp';

    // Detect by response structure
    const responseData = orchestratorResponse.response_data;
    if (responseData) {
      // A2A typically has parts array
      if (responseData.parts || responseData.raw_response?.result?.message?.parts) {
        return 'a2a';
      }
      
      // ACP typically has content field
      if (responseData.content !== undefined || responseData.capabilities) {
        return 'acp';
      }
    }

    return 'unknown';
  }

  /**
   * Fallback content extraction for unknown protocols
   */
  private static extractGenericContent(orchestratorResponse: any): string {
    const candidates = [
      orchestratorResponse.content,
      orchestratorResponse.response_data?.content,
      orchestratorResponse.response_data?.text,
      orchestratorResponse.response_data?.message,
      orchestratorResponse.response_data?.response,
      orchestratorResponse.text,
      orchestratorResponse.message,
    ];

    for (const candidate of candidates) {
      if (typeof candidate === 'string' && candidate.trim()) {
        return candidate.trim();
      }
    }

    // Try to stringify the response data
    if (orchestratorResponse.response_data) {
      try {
        return JSON.stringify(orchestratorResponse.response_data, null, 2);
      } catch {
        // Ignore JSON stringify errors
      }
    }

    return 'Unable to extract content';
  }
}
```

### **Step 4: React Component for ACP Content**

```typescript
// src/components/ACPContent.tsx
import React from 'react';
import { ACPResponseParser, ParsedACPContent } from '../services/acpParser';
import { ExternalLink, Tool, CheckCircle, XCircle } from 'lucide-react';

interface ACPContentProps {
  orchestratorResponse: any;
  className?: string;
}

export const ACPContent: React.FC<ACPContentProps> = ({ 
  orchestratorResponse, 
  className = '' 
}) => {
  const parsed = React.useMemo(() => {
    return ACPResponseParser.parseOrchestratorResponse(orchestratorResponse);
  }, [orchestratorResponse]);

  if (!parsed) {
    return (
      <div className={`text-gray-500 italic ${className}`}>
        Unable to parse ACP response
      </div>
    );
  }

  return (
    <div className={`acp-content ${className}`}>
      {/* Main Content */}
      {parsed.textContent && (
        <div className="prose prose-sm max-w-none mb-4">
          <p>{parsed.textContent}</p>
        </div>
      )}

      {/* Agent Thinking Process */}
      {parsed.thinking && (
        <div className="mb-4 bg-blue-50 p-3 rounded-lg border-l-4 border-blue-400">
          <div className="flex items-start gap-2">
            <div className="text-blue-600 font-semibold text-sm">Agent Thinking:</div>
          </div>
          <p className="text-blue-700 text-sm mt-1">{parsed.thinking}</p>
        </div>
      )}

      {/* Tool Calls */}
      {parsed.toolCalls.length > 0 && (
        <div className="mb-4">
          <h4 className="font-semibold mb-2 flex items-center gap-2">
            <Tool className="w-4 h-4" />
            Tool Calls
          </h4>
          <div className="space-y-2">
            {parsed.toolCalls.map((call, index) => (
              <div key={call.id || index} className="bg-yellow-50 p-3 rounded-lg border-l-4 border-yellow-400">
                <div className="font-mono text-sm">
                  <span className="text-yellow-800 font-semibold">
                    {call.tool}.{call.function}
                  </span>
                  <span className="text-gray-600">
                    ({JSON.stringify(call.parameters, null, 1)})
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tool Results */}
      {parsed.toolResults.length > 0 && (
        <div className="mb-4">
          <h4 className="font-semibold mb-2">Tool Results</h4>
          <div className="space-y-2">
            {parsed.toolResults.map((result, index) => (
              <div key={result.id || index} className={`p-3 rounded-lg border-l-4 ${
                result.error 
                  ? 'bg-red-50 border-red-400' 
                  : 'bg-green-50 border-green-400'
              }`}>
                <div className="flex items-start gap-2">
                  {result.error ? (
                    <XCircle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
                  ) : (
                    <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  )}
                  <div className="min-w-0">
                    {result.error ? (
                      <p className="text-red-700 text-sm">{result.error}</p>
                    ) : (
                      <pre className="text-green-700 text-sm whitespace-pre-wrap">
                        {typeof result.result === 'string' 
                          ? result.result 
                          : JSON.stringify(result.result, null, 2)
                        }
                      </pre>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Attachments */}
      {parsed.attachments.length > 0 && (
        <div className="mb-4">
          <h4 className="font-semibold mb-2">Attachments</h4>
          <div className="grid grid-cols-2 gap-2">
            {parsed.attachments.map((attachment, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-2">
                  <ExternalLink className="w-4 h-4 text-gray-500" />
                  <span className="text-sm font-medium">
                    {attachment.filename || `${attachment.type} attachment`}
                  </span>
                </div>
                {attachment.type === 'image' && attachment.url && (
                  <img 
                    src={attachment.url} 
                    alt={attachment.filename || 'Attachment'}
                    className="w-full h-32 object-cover rounded"
                  />
                )}
                {attachment.url && (
                  <a 
                    href={attachment.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    Open {attachment.type}
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Capabilities */}
      {parsed.capabilities.length > 0 && (
        <div className="mb-4">
          <h4 className="font-semibold mb-2">Agent Capabilities</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {parsed.capabilities.map((capability, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-3">
                <div className="font-medium text-sm">{capability.name}</div>
                <p className="text-gray-600 text-xs mt-1">{capability.description}</p>
                {capability.parameters && (
                  <div className="mt-2">
                    <div className="text-xs text-gray-500 mb-1">Parameters:</div>
                    <div className="text-xs font-mono bg-gray-50 p-1 rounded">
                      {Object.keys(capability.parameters).join(', ')}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Status Indicator */}
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <div className={`w-2 h-2 rounded-full ${
          parsed.status === 'ready' ? 'bg-green-400' :
          parsed.status === 'working' ? 'bg-yellow-400' :
          parsed.status === 'error' ? 'bg-red-400' :
          'bg-gray-400'
        }`} />
        Status: {parsed.status}
      </div>
    </div>
  );
};
```

### **Step 5: Updated Orchestrator API Integration**

```typescript
// src/services/orchestratorApi.ts - Updated with unified parsing
import { UnifiedProtocolParser } from './protocolParser';

export class OrchestratorAPI {
  // ... existing methods ...

  /**
   * Extract content using unified protocol parser
   */
  public extractResponseContent(data: any): string {
    const parsed = UnifiedProtocolParser.parseResponse(data);
    
    // Log any parsing errors in development
    if (parsed.errors.length > 0 && process.env.NODE_ENV === 'development') {
      console.warn('Protocol parsing errors:', parsed.errors);
    }
    
    return parsed.textContent;
  }

  /**
   * Get full parsed response for advanced UI components
   */
  public parseResponse(data: any) {
    return UnifiedProtocolParser.parseResponse(data);
  }
}
```

## 🧪 **Testing ACP Parser**

### **Unit Tests**

```typescript
// src/services/__tests__/acpParser.test.ts
import { ACPResponseParser } from '../acpParser';

describe('ACPResponseParser', () => {
  describe('parseACPResponse', () => {
    it('should parse basic ACP response', () => {
      const response = {
        content: 'Hello, how can I help you?',
        metadata: {
          agent_id: 'acp-hello',
          agent_name: 'Hello Agent',
        },
        status: 'ready',
      };

      const result = ACPResponseParser.parseACPResponse(response);

      expect(result.textContent).toBe('Hello, how can I help you?');
      expect(result.metadata.agent_id).toBe('acp-hello');
      expect(result.status).toBe('ready');
    });

    it('should parse tool calls', () => {
      const response = {
        content: 'I will calculate that for you.',
        tool_calls: [
          {
            id: 'call_1',
            tool: 'calculator',
            function: 'add',
            parameters: { a: 5, b: 3 },
          },
        ],
        metadata: { agent_id: 'acp-calc' },
      };

      const result = ACPResponseParser.parseACPResponse(response);

      expect(result.toolCalls).toHaveLength(1);
      expect(result.toolCalls[0]).toEqual({
        id: 'call_1',
        tool: 'calculator',
        function: 'add',
        parameters: { a: 5, b: 3 },
      });
    });

    it('should handle capabilities', () => {
      const response = {
        content: 'I can help with math.',
        capabilities: [
          {
            name: 'add',
            description: 'Add two numbers',
            parameters: {
              a: { type: 'number' },
              b: { type: 'number' },
            },
          },
        ],
        metadata: { agent_id: 'acp-math' },
      };

      const result = ACPResponseParser.parseACPResponse(response);

      expect(result.capabilities).toHaveLength(1);
      expect(result.capabilities[0].name).toBe('add');
      expect(result.capabilities[0].description).toBe('Add two numbers');
    });
  });

  describe('parseOrchestratorResponse', () => {
    it('should handle orchestrator-wrapped ACP response', () => {
      const orchestratorResponse = {
        agent_id: 'acp-hello',
        protocol: 'acp',
        response_data: {
          content: 'Hello from ACP agent!',
          metadata: {
            agent_id: 'acp-hello',
            response_type: 'greeting',
          },
        },
      };

      const result = ACPResponseParser.parseOrchestratorResponse(orchestratorResponse);

      expect(result).not.toBeNull();
      expect(result!.textContent).toBe('Hello from ACP agent!');
      expect(result!.metadata.response_type).toBe('greeting');
    });

    it('should handle simple string responses', () => {
      const orchestratorResponse = {
        agent_id: 'acp-simple',
        response_data: 'Simple text response',
      };

      const result = ACPResponseParser.parseOrchestratorResponse(orchestratorResponse);

      expect(result).not.toBeNull();
      expect(result!.textContent).toBe('Simple text response');
      expect(result!.metadata.agent_id).toBe('acp-simple');
    });
  });
});
```

### **Integration Tests with Unified Parser**

```typescript
// src/services/__tests__/protocolParser.integration.test.ts
import { UnifiedProtocolParser } from '../protocolParser';

describe('UnifiedProtocolParser Integration', () => {
  it('should handle real ACP hello world response', () => {
    const response = {
      request_id: 'req_acp_1',
      agent_id: 'acp-hello-world',
      protocol: 'acp',
      response_data: {
        content: 'Hello there! I\'m the ACP Hello World agent.',
        metadata: {
          agent_id: 'acp-hello-world',
          version: '1.0.0',
        },
        capabilities: [
          {
            name: 'greet',
            description: 'Provide friendly greetings',
          },
        ],
      },
    };

    const parsed = UnifiedProtocolParser.parseResponse(response);

    expect(parsed.protocol).toBe('acp');
    expect(parsed.textContent).toContain('Hello there!');
    expect(parsed.acpContent).not.toBeUndefined();
    expect(parsed.acpContent!.capabilities).toHaveLength(1);
    expect(parsed.errors).toHaveLength(0);
  });

  it('should detect protocol automatically', () => {
    const a2aResponse = {
      agent_id: 'a2a-math-agent',
      response_data: {
        raw_response: {
          message: {
            parts: [{ kind: 'text', text: 'A2A response' }],
          },
        },
      },
    };

    const acpResponse = {
      agent_id: 'acp-hello-world', 
      response_data: {
        content: 'ACP response',
      },
    };

    const a2aParsed = UnifiedProtocolParser.parseResponse(a2aResponse);
    const acpParsed = UnifiedProtocolParser.parseResponse(acpResponse);

    expect(a2aParsed.protocol).toBe('a2a');
    expect(acpParsed.protocol).toBe('acp');
  });
});
```

## 🎯 **Key Takeaways**

1. **ACP is simpler than A2A** - Direct content field vs structured parts
2. **Tool support is built-in** - ACP has native tool calling capabilities
3. **Unified parsing is powerful** - Handle multiple protocols transparently
4. **Metadata matters** - ACP provides rich agent metadata and thinking
5. **Status tracking** - ACP supports agent status (ready, working, error)
6. **Fallback strategies** - Always provide graceful degradation
7. **Protocol detection** - Automatically identify protocol from response structure

---

**Next**: [03-unified-protocol-handling.md](./03-unified-protocol-handling.md) - Building Protocol-Agnostic Components

**Previous**: [01-a2a-response-handling.md](./01-a2a-response-handling.md)