# Phase 2.2: Building Robust Service Layer Architecture

## 🎯 **Learning Objectives**

By the end of this tutorial, you will:
- Understand why service layers are crucial for maintainable applications
- Build a complete API service with error handling and protocol awareness
- Implement proper separation of concerns between UI and data access
- Master TypeScript interfaces for API communication
- Create testable and mockable service architecture

## 🏗️ **What is a Service Layer?**

A **service layer** is an abstraction that sits between your React components and external APIs. It handles:

```
React Components  ←→  Service Layer  ←→  External APIs
     (UI Logic)      (Business Logic)    (Data Sources)
```

### **Why Not Call APIs Directly in Components?**

```typescript
// ❌ Bad: API calls mixed with UI logic
const ChatComponent = () => {
  const [message, setMessage] = useState('');
  
  const handleSend = async () => {
    try {
      // Mixed concerns: UI component knows about HTTP, URLs, error handling
      const response = await fetch('http://localhost:8004/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: message }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      
      // Protocol-specific parsing logic in UI component
      let content = '';
      if (data.protocol === 'a2a') {
        content = data.response_data.raw_response.parts
          .filter(part => part.kind === 'text')
          .map(part => part.text)
          .join(' ');
      } else if (data.protocol === 'acp') {
        content = data.response_data.content || data.content;
      }
      
      // More UI logic...
    } catch (error) {
      // Error handling mixed with UI
      setError(error.message);
    }
  };
  
  return <div>{/* UI logic */}</div>;
};

// ✅ Good: Clean separation of concerns
const ChatComponent = () => {
  const [message, setMessage] = useState('');
  
  const handleSend = async () => {
    try {
      // UI component only knows about business operations
      const response = await orchestratorApi.processMessage(message);
      setResponse(response.content); // Clean, parsed content
    } catch (error) {
      setError(error.message); // Normalized error message
    }
  };
  
  return <div>{/* Pure UI logic */}</div>;
};
```

## 🛠️ **Building Our Service Layer: OrchestratorAPI**

Let's build our complete service layer step by step:

### **Step 1: Base Service Class Structure**

```typescript
// src/services/orchestratorApi.ts
export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  agents_discovered: number;
  timestamp: string;
}

export interface AgentSummary {
  agent_id: string;
  name: string;
  protocol: string;
  endpoint: string;
  status: string;
  capabilities: Array<{
    name: string;
    description?: string;
    tags: string[];
  }>;
}

export interface ProcessResponse {
  request_id: string;
  agent_id: string;
  agent_name: string;
  protocol: string;
  content: string;              // ← Parsed, clean content ready for UI
  confidence: number;
  reasoning?: string;
  response_data: any;          // ← Raw protocol response
  success: boolean;
  duration_ms: number;
  timestamp: string;
}

class OrchestratorAPI {
  private baseUrl: string;
  
  constructor(baseUrl = 'http://localhost:8004') {
    this.baseUrl = baseUrl;
  }
  
  // ... methods will go here
}

// Export singleton instance
export const orchestratorApi = new OrchestratorAPI();
```

### **Step 2: HTTP Request Management**

```typescript
class OrchestratorAPI {
  private async makeRequest<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    // Set default headers
    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      // Add timeout
      signal: AbortSignal.timeout(30000), // 30 second timeout
      ...options,
    };
    
    try {
      const response = await fetch(url, defaultOptions);
      
      // Handle HTTP errors
      if (!response.ok) {
        await this.handleHttpError(response);
      }
      
      // Parse JSON response
      return await response.json();
      
    } catch (error) {
      // Convert all errors to our standard format
      throw this.normalizeError(error);
    }
  }
  
  private async handleHttpError(response: Response): Promise<never> {
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
    
    try {
      // Try to get error details from response body
      const errorData = await response.json();
      if (errorData.detail) {
        errorMessage = errorData.detail;
      } else if (errorData.message) {
        errorMessage = errorData.message;
      }
    } catch {
      // If JSON parsing fails, use status text
    }
    
    // Create specific error types
    switch (response.status) {
      case 400:
        throw new Error(`Bad Request: ${errorMessage}`);
      case 401:
        throw new Error('Authentication required');
      case 403:
        throw new Error('Access forbidden');
      case 404:
        throw new Error('Orchestrator not found. Is it running on port 8004?');
      case 429:
        throw new Error('Too many requests. Please wait a moment.');
      case 500:
        throw new Error('Internal server error. Please try again.');
      case 502:
      case 503:
      case 504:
        throw new Error('Orchestrator is temporarily unavailable');
      default:
        throw new Error(errorMessage);
    }
  }
  
  private normalizeError(error: unknown): Error {
    if (error instanceof Error) {
      // Network errors, timeouts, etc.
      if (error.name === 'AbortError') {
        return new Error('Request timed out. Please try again.');
      }
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        return new Error('Unable to connect to orchestrator. Check your connection.');
      }
      return error;
    }
    
    return new Error('An unexpected error occurred');
  }
}
```

### **Step 3: API Methods**

```typescript
class OrchestratorAPI {
  // ... previous methods ...
  
  async checkHealth(): Promise<HealthResponse> {
    return this.makeRequest<HealthResponse>('/health');
  }
  
  async getAgents(): Promise<AgentSummary[]> {
    return this.makeRequest<AgentSummary[]>('/agents');
  }
  
  async getAgentsByCapability(capability: string): Promise<AgentSummary[]> {
    return this.makeRequest<AgentSummary[]>(`/agents?capability=${encodeURIComponent(capability)}`);
  }
  
  async processMessage(query: string): Promise<ProcessResponse> {
    const response = await this.makeRequest<any>('/process', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
    
    // Parse the response and extract clean content
    return this.parseProcessResponse(response);
  }
  
  async refreshAgents(): Promise<void> {
    await this.makeRequest<void>('/agents/refresh', {
      method: 'POST',
    });
  }
}
```

### **Step 4: Protocol-Aware Response Parsing**

This is the most important part - handling different protocol response formats:

```typescript
class OrchestratorAPI {
  // ... previous methods ...
  
  private parseProcessResponse(rawResponse: any): ProcessResponse {
    // Extract clean content using our protocol parsing
    const content = this.extractResponseContent(rawResponse);
    
    return {
      request_id: rawResponse.request_id || 'unknown',
      agent_id: rawResponse.agent_id || 'unknown',
      agent_name: rawResponse.agent_name || 'Unknown Agent',
      protocol: rawResponse.protocol || 'unknown',
      content, // ← Clean, UI-ready content
      confidence: rawResponse.confidence || 0,
      reasoning: rawResponse.reasoning,
      response_data: rawResponse.response_data,
      success: rawResponse.success ?? true,
      duration_ms: rawResponse.duration_ms || 0,
      timestamp: rawResponse.timestamp || new Date().toISOString(),
    };
  }
  
  // This method handles the complexity of different protocol formats
  public extractResponseContent(data: any): string {
    const responseData = data.response_data;
    const protocol = data.protocol?.toLowerCase();
    
    // A2A Protocol: Uses "parts" array structure
    if (protocol === 'a2a' && responseData?.raw_response?.parts?.length > 0) {
      const textParts = responseData.raw_response.parts
        .filter((part: any) => part.kind === 'text' || !part.kind)
        .map((part: any) => part.text)
        .filter(Boolean);
      
      if (textParts.length > 0) {
        return textParts.join(' ').trim();
      }
    }
    
    // ACP Protocol: More direct response format  
    if (protocol === 'acp') {
      if (responseData?.content) {
        return responseData.content;
      }
      if (responseData?.response && typeof responseData.response === 'string') {
        return responseData.response;
      }
      if (responseData?.output) {
        return responseData.output;
      }
    }
    
    // MCP Protocol: Future support
    if (protocol === 'mcp') {
      // Will implement when MCP agents are added
      if (responseData?.text) {
        return responseData.text;
      }
    }
    
    // Fallback: Try to find any text content
    if (data.content && typeof data.content === 'string') {
      return data.content;
    }
    
    if (responseData && typeof responseData === 'string') {
      return responseData;
    }
    
    // Last resort: stringify the response
    if (responseData) {
      try {
        return JSON.stringify(responseData, null, 2);
      } catch {
        // If JSON.stringify fails, return placeholder
      }
    }
    
    return 'No response content available';
  }
}
```

## 🧪 **Testing Your Service Layer**

### **Unit Testing with Jest**

```typescript
// src/services/__tests__/orchestratorApi.test.ts
import { OrchestratorAPI } from '../orchestratorApi';

// Mock fetch globally
global.fetch = jest.fn();

describe('OrchestratorAPI', () => {
  let api: OrchestratorAPI;
  
  beforeEach(() => {
    api = new OrchestratorAPI('http://test-api');
    jest.clearAllMocks();
  });
  
  describe('checkHealth', () => {
    it('should return health status', async () => {
      const mockResponse = { status: 'healthy', agents_discovered: 2 };
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });
      
      const result = await api.checkHealth();
      
      expect(fetch).toHaveBeenCalledWith('http://test-api/health', expect.any(Object));
      expect(result).toEqual(mockResponse);
    });
    
    it('should handle network errors', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new TypeError('Network error'));
      
      await expect(api.checkHealth()).rejects.toThrow(
        'Unable to connect to orchestrator'
      );
    });
  });
  
  describe('extractResponseContent', () => {
    it('should parse A2A protocol responses', () => {
      const a2aResponse = {
        protocol: 'a2a',
        response_data: {
          raw_response: {
            parts: [
              { kind: 'text', text: 'The answer is ' },
              { kind: 'text', text: '42' }
            ]
          }
        }
      };
      
      const result = api.extractResponseContent(a2aResponse);
      expect(result).toBe('The answer is 42');
    });
    
    it('should parse ACP protocol responses', () => {
      const acpResponse = {
        protocol: 'acp',
        response_data: {
          content: 'Hello from ACP agent!'
        }
      };
      
      const result = api.extractResponseContent(acpResponse);
      expect(result).toBe('Hello from ACP agent!');
    });
    
    it('should handle malformed responses gracefully', () => {
      const badResponse = {
        protocol: 'unknown',
        response_data: null
      };
      
      const result = api.extractResponseContent(badResponse);
      expect(result).toBe('No response content available');
    });
  });
});
```

### **Integration Testing**

```typescript
// src/services/__tests__/orchestratorApi.integration.test.ts
import { orchestratorApi } from '../orchestratorApi';

describe('OrchestratorAPI Integration', () => {
  // Only run if orchestrator is running
  const isOrchestratorRunning = process.env.TEST_WITH_REAL_API === 'true';
  
  it.skipIf(!isOrchestratorRunning)('should connect to real orchestrator', async () => {
    const health = await orchestratorApi.checkHealth();
    expect(health.status).toBe('healthy');
  });
  
  it.skipIf(!isOrchestratorRunning)('should process real messages', async () => {
    const response = await orchestratorApi.processMessage('What is 2 + 2?');
    expect(response.content).toContain('4');
    expect(response.agent_id).toBeTruthy();
  });
});
```

## 🔧 **Advanced Service Patterns**

### **Request/Response Interceptors**

```typescript
class OrchestratorAPI {
  private requestInterceptors: Array<(config: RequestInit) => RequestInit> = [];
  private responseInterceptors: Array<(response: any) => any> = [];
  
  addRequestInterceptor(interceptor: (config: RequestInit) => RequestInit) {
    this.requestInterceptors.push(interceptor);
  }
  
  addResponseInterceptor(interceptor: (response: any) => any) {
    this.responseInterceptors.push(interceptor);
  }
  
  private async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    // Apply request interceptors
    let config = { ...options };
    for (const interceptor of this.requestInterceptors) {
      config = interceptor(config);
    }
    
    const response = await fetch(`${this.baseUrl}${endpoint}`, config);
    let data = await response.json();
    
    // Apply response interceptors
    for (const interceptor of this.responseInterceptors) {
      data = interceptor(data);
    }
    
    return data;
  }
}

// Usage: Add logging interceptor
orchestratorApi.addRequestInterceptor((config) => {
  console.log('API Request:', config);
  return config;
});

orchestratorApi.addResponseInterceptor((response) => {
  console.log('API Response:', response);
  return response;
});
```

### **Caching Layer**

```typescript
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number; // Time to live in milliseconds
}

class CachedOrchestratorAPI extends OrchestratorAPI {
  private cache = new Map<string, CacheEntry<any>>();
  
  private getCacheKey(endpoint: string, options: RequestInit): string {
    return `${endpoint}:${JSON.stringify(options)}`;
  }
  
  private isValidCacheEntry<T>(entry: CacheEntry<T>): boolean {
    return Date.now() - entry.timestamp < entry.ttl;
  }
  
  async getAgents(): Promise<AgentSummary[]> {
    const cacheKey = this.getCacheKey('/agents', {});
    const cached = this.cache.get(cacheKey);
    
    if (cached && this.isValidCacheEntry(cached)) {
      console.log('Returning cached agents');
      return cached.data;
    }
    
    // Fetch fresh data
    const agents = await super.getAgents();
    
    // Cache for 30 seconds
    this.cache.set(cacheKey, {
      data: agents,
      timestamp: Date.now(),
      ttl: 30000,
    });
    
    return agents;
  }
  
  invalidateCache(pattern?: string) {
    if (!pattern) {
      this.cache.clear();
      return;
    }
    
    // Remove entries matching pattern
    for (const key of this.cache.keys()) {
      if (key.includes(pattern)) {
        this.cache.delete(key);
      }
    }
  }
}
```

### **Retry Logic**

```typescript
class ResilientOrchestratorAPI extends OrchestratorAPI {
  private async makeRequestWithRetry<T>(
    endpoint: string,
    options: RequestInit = {},
    maxRetries = 3
  ): Promise<T> {
    let lastError: Error;
    
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        return await this.makeRequest<T>(endpoint, options);
      } catch (error) {
        lastError = error as Error;
        
        // Don't retry certain errors
        if (error.message.includes('400') || error.message.includes('401')) {
          throw error;
        }
        
        // Wait longer between retries
        if (attempt < maxRetries - 1) {
          const delay = Math.min(1000 * Math.pow(2, attempt), 5000);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    
    throw new Error(`Request failed after ${maxRetries} attempts: ${lastError.message}`);
  }
  
  async processMessage(query: string): Promise<ProcessResponse> {
    return this.makeRequestWithRetry('/process', {
      method: 'POST',
      body: JSON.stringify({ query }),
    }).then(response => this.parseProcessResponse(response));
  }
}
```

## 🏭 **Production Considerations**

### **Environment Configuration**

```typescript
// src/config/apiConfig.ts
interface ApiConfig {
  baseUrl: string;
  timeout: number;
  retries: number;
  enableCaching: boolean;
}

const getApiConfig = (): ApiConfig => {
  const env = process.env.NODE_ENV;
  
  switch (env) {
    case 'development':
      return {
        baseUrl: 'http://localhost:8004',
        timeout: 30000,
        retries: 1,
        enableCaching: false,
      };
    
    case 'production':
      return {
        baseUrl: process.env.REACT_APP_API_URL || 'https://api.example.com',
        timeout: 10000,
        retries: 3,
        enableCaching: true,
      };
    
    case 'test':
      return {
        baseUrl: 'http://test-api',
        timeout: 5000,
        retries: 0,
        enableCaching: false,
      };
    
    default:
      throw new Error(`Unknown environment: ${env}`);
  }
};

// Create API instance with environment config
const config = getApiConfig();
export const orchestratorApi = new OrchestratorAPI(config.baseUrl);
```

### **Monitoring and Analytics**

```typescript
class MonitoredOrchestratorAPI extends OrchestratorAPI {
  private metrics = {
    requestCount: 0,
    errorCount: 0,
    totalLatency: 0,
  };
  
  private async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const startTime = Date.now();
    this.metrics.requestCount++;
    
    try {
      const result = await super.makeRequest<T>(endpoint, options);
      const latency = Date.now() - startTime;
      this.metrics.totalLatency += latency;
      
      // Send metrics to monitoring service
      this.trackEvent('api_request_success', {
        endpoint,
        latency,
        timestamp: Date.now(),
      });
      
      return result;
    } catch (error) {
      this.metrics.errorCount++;
      
      // Track errors
      this.trackEvent('api_request_error', {
        endpoint,
        error: error.message,
        timestamp: Date.now(),
      });
      
      throw error;
    }
  }
  
  private trackEvent(event: string, data: any) {
    // Send to analytics service (e.g., Google Analytics, Mixpanel)
    console.log('Analytics:', event, data);
  }
  
  getMetrics() {
    return {
      ...this.metrics,
      averageLatency: this.metrics.requestCount > 0 
        ? this.metrics.totalLatency / this.metrics.requestCount 
        : 0,
      errorRate: this.metrics.requestCount > 0
        ? this.metrics.errorCount / this.metrics.requestCount
        : 0,
    };
  }
}
```

## 🎯 **Key Takeaways**

1. **Service layers separate concerns** - Keep API logic out of React components
2. **Handle errors gracefully** - Convert all errors to user-friendly messages  
3. **Protocol awareness is crucial** - Different agents return different response formats
4. **Make services testable** - Use dependency injection and mockable interfaces
5. **Add retry logic** - Networks fail, services have outages
6. **Cache when appropriate** - Don't spam APIs with repeated requests
7. **Monitor in production** - Track errors, latency, and usage patterns

## 📋 **Next Steps**

In the next tutorial, we'll build custom React hooks that use our service layer:
- **useOrchestrator Hook**: State management for API integration  
- **Error handling patterns**: User-friendly error states
- **Loading indicators**: Professional UX during API calls
- **Real-time health monitoring**: Connection status indicators

## 🔗 **Helpful Resources**

- [Fetch API Documentation](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- [TypeScript Utility Types](https://www.typescriptlang.org/docs/handbook/utility-types.html)
- [Jest Testing Framework](https://jestjs.io/docs/getting-started)
- [Error Handling Best Practices](https://web.dev/reliable/)

---

**Next**: [03-hooks-for-api-state.md](./03-hooks-for-api-state.md) - Custom Hooks for API State Management

**Previous**: [01-orchestrator-api-basics.md](./01-orchestrator-api-basics.md)