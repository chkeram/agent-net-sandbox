# Troubleshooting: API Integration Debugging

## 🎯 **What You'll Learn**

This comprehensive debugging guide covers:
- Common API integration failures and their root causes
- Step-by-step debugging methodology for React applications
- Browser developer tools mastery for API troubleshooting
- Production vs development environment differences
- Error handling and user experience patterns

## 🔍 **Debugging Methodology: The TRACE Approach**

Use this systematic approach for all API integration issues:

### **T** - **Test** the Backend First
### **R** - **Review** Network Requests  
### **A** - **Analyze** Frontend State
### **C** - **Check** Error Handling
### **E** - **Examine** Environment Differences

## 🚨 **Issue 1: API Calls Return 404 "Not Found"**

### **Symptoms**
```javascript
// Browser console shows:
GET http://localhost:8004/health 404 (Not Found)
POST http://localhost:8004/process 404 (Not Found)

// React error state:
"Orchestrator service not found. Please ensure it's running on port 8004."
```

### **Debugging Steps**

#### **Step 1: Verify Backend is Running**
```bash
# Check if orchestrator is running
curl -v http://localhost:8004/health

# If connection refused:
# curl: (7) Failed to connect to localhost port 8004: Connection refused

# Check what's running on port 8004
netstat -an | grep 8004
# Or on macOS:
lsof -i :8004

# Start the orchestrator if not running
cd agents/orchestrator
source venv/bin/activate
uvicorn orchestrator.api:app --reload --host 127.0.0.1 --port 8004
```

#### **Step 2: Verify API Endpoints**
```bash
# Test each endpoint manually
curl http://localhost:8004/health
curl http://localhost:8004/agents  
curl -X POST http://localhost:8004/process \
  -H "Content-Type: application/json" \
  -d '{"query": "hello"}'

# Check FastAPI auto-generated docs
open http://localhost:8004/docs
```

#### **Step 3: Check Frontend API Configuration**
```typescript
// src/services/orchestratorApi.ts
export class OrchestratorAPI {
  constructor(baseUrl = 'http://localhost:8004') {
    this.baseUrl = baseUrl;
    console.log('🔗 API Base URL:', this.baseUrl); // Debug log
  }
  
  async checkHealth(): Promise<HealthResponse> {
    const url = `${this.baseUrl}/health`;
    console.log('🩺 Health check URL:', url); // Debug log
    
    try {
      const response = await fetch(url);
      console.log('🩺 Health response:', response.status, response.statusText);
      return await response.json();
    } catch (error) {
      console.error('🩺 Health check failed:', error);
      throw error;
    }
  }
}
```

#### **Step 4: Environment Variable Issues**
```typescript
// Check environment configuration
console.log('Environment:', process.env.NODE_ENV);
console.log('API URL:', process.env.REACT_APP_API_URL);

// .env.local (for local development)
REACT_APP_API_URL=http://localhost:8004

// .env.production (for production)
REACT_APP_API_URL=https://your-api-domain.com

// Use in code:
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8004';
```

## 🌐 **Issue 2: CORS (Cross-Origin Resource Sharing) Errors**

### **Symptoms**
```javascript
// Browser console shows:
Access to fetch at 'http://localhost:8004/health' from origin 'http://localhost:5173' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present

// Or:
CORS policy: The request client is not a secure context and the resource is in a 
more-private address space `local`
```

### **Debugging Steps**

#### **Step 1: Understand the CORS Error**
```javascript
// Open browser dev tools → Console
// Look for the exact CORS error message

// Common CORS error types:
// 1. Missing Access-Control-Allow-Origin header
// 2. Preflight request failed
// 3. Credentials not allowed
// 4. Method not allowed
// 5. Header not allowed
```

#### **Step 2: Check Backend CORS Configuration**
```python
# agents/orchestrator/orchestrator/api.py
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Create React App
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=False,  # Set to True if you need credentials
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

#### **Step 3: Test CORS with curl**
```bash
# Test preflight request (OPTIONS)
curl -X OPTIONS http://localhost:8004/process \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v

# Should return CORS headers:
# Access-Control-Allow-Origin: http://localhost:5173
# Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
# Access-Control-Allow-Headers: *
```

#### **Step 4: Frontend CORS Workarounds**

```typescript
// vite.config.ts - Development proxy to avoid CORS
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8004',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
        configure: (proxy, options) => {
          proxy.on('error', (err, req, res) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyRes', (proxyRes, req, res) => {
            console.log('Received response from target:', proxyRes.statusCode, req.url);
          });
        },
      },
    },
  },
});
```

```typescript
// Update API service to use proxy in development
export class OrchestratorAPI {
  private baseUrl: string;
  
  constructor() {
    if (process.env.NODE_ENV === 'development') {
      this.baseUrl = '/api'; // Use proxy
    } else {
      this.baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8004';
    }
  }
}
```

## ⏱️ **Issue 3: Request Timeouts and Slow Responses**

### **Symptoms**
```javascript
// Browser console:
TypeError: Failed to fetch
// After 30-120 seconds

// Or in Network tab:
Status: (failed) net::ERR_NETWORK_IO_SUSPENDED
```

### **Debugging Steps**

#### **Step 1: Identify Timeout Source**
```typescript
// Add detailed timing logs
export class TimingAwareOrchestratorAPI extends OrchestratorAPI {
  async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const startTime = performance.now();
    const timeoutDuration = 30000; // 30 seconds
    
    console.log(`🕐 Starting request to ${endpoint} at ${new Date().toISOString()}`);
    
    // Create AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      console.log(`⏰ Request to ${endpoint} timed out after ${timeoutDuration}ms`);
      controller.abort();
    }, timeoutDuration);
    
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        signal: controller.signal,
      });
      
      const duration = performance.now() - startTime;
      console.log(`✅ Request to ${endpoint} completed in ${duration.toFixed(2)}ms`);
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
      
    } catch (error) {
      const duration = performance.now() - startTime;
      console.error(`❌ Request to ${endpoint} failed after ${duration.toFixed(2)}ms:`, error);
      
      clearTimeout(timeoutId);
      
      if (error.name === 'AbortError') {
        throw new Error(`Request timed out after ${timeoutDuration}ms`);
      }
      
      throw error;
    }
  }
}
```

#### **Step 2: Backend Performance Analysis**
```bash
# Test backend response time directly
time curl -X POST http://localhost:8004/process \
  -H "Content-Type: application/json" \
  -d '{"query": "What is 2 + 2?"}'

# Monitor backend logs for slow queries
docker-compose logs -f orchestrator | grep -E "(WARNING|ERROR|slow)"

# Check system resources
htop  # or top on macOS
docker stats  # if using Docker
```

#### **Step 3: Network Throttling Test**
```javascript
// Test with simulated slow network
// Chrome DevTools → Network → Throttling → Slow 3G

// Or programmatically test with delays
export class ThrottleTestAPI extends OrchestratorAPI {
  async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    // Simulate network delay for testing
    if (process.env.NODE_ENV === 'development' && process.env.REACT_APP_SIMULATE_SLOW_NETWORK) {
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    return super.makeRequest(endpoint, options);
  }
}
```

#### **Step 4: Implement Progressive Timeouts**
```typescript
export class AdaptiveTimeoutAPI extends OrchestratorAPI {
  private timeoutHistory: number[] = [];
  private readonly maxHistorySize = 10;
  
  private calculateAdaptiveTimeout(): number {
    if (this.timeoutHistory.length === 0) {
      return 30000; // Default 30 seconds
    }
    
    // Use 95th percentile of recent response times, with minimum 10s
    const sorted = [...this.timeoutHistory].sort((a, b) => a - b);
    const percentile95 = sorted[Math.floor(sorted.length * 0.95)];
    
    return Math.max(percentile95 * 2, 10000); // At least 10 seconds
  }
  
  async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const timeout = this.calculateAdaptiveTimeout();
    const startTime = performance.now();
    
    try {
      const result = await super.makeRequest(endpoint, { ...options, timeout });
      
      // Record successful response time
      const duration = performance.now() - startTime;
      this.timeoutHistory.push(duration);
      
      // Keep history size manageable
      if (this.timeoutHistory.length > this.maxHistorySize) {
        this.timeoutHistory.shift();
      }
      
      return result;
    } catch (error) {
      // Don't record failed requests in timing history
      throw error;
    }
  }
}
```

## 🔒 **Issue 4: Authentication and Authorization Problems**

### **Symptoms**
```javascript
// HTTP 401 Unauthorized
// HTTP 403 Forbidden
// HTTP 422 Unprocessable Entity (validation errors)
```

### **Debugging Steps**

#### **Step 1: Check Request Headers**
```typescript
// Add request/response logging
export class DebuggingOrchestratorAPI extends OrchestratorAPI {
  async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    console.group(`🔍 API Request: ${endpoint}`);
    console.log('📤 Request options:', {
      method: options.method || 'GET',
      headers: options.headers,
      body: options.body,
    });
    
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, options);
      
      console.log('📥 Response status:', response.status, response.statusText);
      console.log('📥 Response headers:', Object.fromEntries(response.headers.entries()));
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('📥 Error response body:', errorText);
        console.groupEnd();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }
      
      const data = await response.json();
      console.log('📥 Response data:', data);
      console.groupEnd();
      
      return data;
    } catch (error) {
      console.error('📥 Request failed:', error);
      console.groupEnd();
      throw error;
    }
  }
}
```

#### **Step 2: Validate Request Body**
```typescript
// Add request validation
export class ValidatingOrchestratorAPI extends OrchestratorAPI {
  async processMessage(query: string): Promise<ProcessResponse> {
    // Validate input
    if (!query || typeof query !== 'string') {
      throw new Error('Query must be a non-empty string');
    }
    
    if (query.trim().length === 0) {
      throw new Error('Query cannot be empty or whitespace only');
    }
    
    if (query.length > 10000) {
      throw new Error('Query too long (max 10,000 characters)');
    }
    
    const requestBody = { query: query.trim() };
    console.log('🔍 Validated request body:', requestBody);
    
    return this.makeRequest<ProcessResponse>('/process', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });
  }
}
```

## 📊 **Issue 5: Response Parsing and Data Format Issues**

### **Symptoms**
```javascript
// "Unable to parse response data"
// "Unexpected token < in JSON at position 0" (HTML error page returned)
// Component shows "No content available" despite successful API call
```

### **Debugging Steps**

#### **Step 1: Inspect Raw Response**
```typescript
export class ResponseDebuggingAPI extends OrchestratorAPI {
  async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, options);
    
    // Log raw response details
    console.log('Raw response status:', response.status);
    console.log('Raw response headers:', Object.fromEntries(response.headers.entries()));
    
    // Check content type
    const contentType = response.headers.get('content-type');
    console.log('Response content type:', contentType);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Error response body (raw):', errorText);
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    // Clone response to read both as text and JSON
    const responseClone = response.clone();
    const rawText = await responseClone.text();
    console.log('Raw response text:', rawText);
    
    // Validate it's JSON
    if (!contentType?.includes('application/json')) {
      console.warn('Response is not JSON:', contentType);
      throw new Error(`Expected JSON response, got ${contentType}`);
    }
    
    try {
      const data = await response.json();
      console.log('Parsed JSON data:', data);
      return data;
    } catch (parseError) {
      console.error('JSON parsing failed:', parseError);
      console.error('Raw text that failed to parse:', rawText);
      throw new Error('Invalid JSON response from server');
    }
  }
}
```

#### **Step 2: Protocol-Specific Debugging**
```typescript
// Enhanced protocol debugging
export class ProtocolDebuggingAPI extends OrchestratorAPI {
  extractResponseContent(data: any): string {
    console.group('🔍 Protocol Content Extraction');
    console.log('Input data:', data);
    console.log('Detected protocol:', data.protocol);
    
    try {
      // Try protocol-specific extraction
      const content = super.extractResponseContent(data);
      console.log('✅ Extracted content:', content);
      console.groupEnd();
      return content;
    } catch (error) {
      console.error('❌ Content extraction failed:', error);
      
      // Detailed debugging for each protocol
      if (data.protocol === 'a2a') {
        console.log('A2A debugging:');
        console.log('  response_data:', data.response_data);
        console.log('  raw_response:', data.response_data?.raw_response);
        console.log('  parts:', data.response_data?.raw_response?.result?.message?.parts);
      } else if (data.protocol === 'acp') {
        console.log('ACP debugging:');
        console.log('  response_data:', data.response_data);
        console.log('  content field:', data.response_data?.content);
        console.log('  response field:', data.response_data?.response);
      }
      
      console.groupEnd();
      throw error;
    }
  }
}
```

#### **Step 3: Test with Known Good Data**
```typescript
// Create test fixtures for debugging
export const TEST_RESPONSES = {
  a2a: {
    request_id: 'test-a2a',
    protocol: 'a2a',
    agent_id: 'a2a-math-agent',
    response_data: {
      raw_response: {
        result: {
          message: {
            role: 'assistant',
            parts: [
              { kind: 'text', text: 'Test A2A response' }
            ]
          }
        }
      }
    }
  },
  
  acp: {
    request_id: 'test-acp',
    protocol: 'acp',
    agent_id: 'acp-hello',
    response_data: {
      content: 'Test ACP response'
    }
  }
};

// Test parsing with fixtures
const testParsing = () => {
  const api = new OrchestratorAPI();
  
  console.log('Testing A2A parsing:');
  try {
    const a2aContent = api.extractResponseContent(TEST_RESPONSES.a2a);
    console.log('✅ A2A content:', a2aContent);
  } catch (error) {
    console.error('❌ A2A parsing failed:', error);
  }
  
  console.log('Testing ACP parsing:');
  try {
    const acpContent = api.extractResponseContent(TEST_RESPONSES.acp);
    console.log('✅ ACP content:', acpContent);
  } catch (error) {
    console.error('❌ ACP parsing failed:', error);
  }
};

// Run tests in development
if (process.env.NODE_ENV === 'development') {
  testParsing();
}
```

## 🛠️ **Browser Developer Tools Mastery**

### **Network Tab Analysis**

#### **1. Request/Response Headers**
```javascript
// What to look for in Network tab:
// 1. Status code (200, 404, 500, etc.)
// 2. Response time (should be < 5 seconds for good UX)
// 3. Request headers (Content-Type, Authorization, Origin)
// 4. Response headers (Content-Type, CORS headers, Cache-Control)
// 5. Request payload (POST body)
// 6. Response payload (JSON structure)

// Copy request as curl for backend testing:
// Right-click request → Copy → Copy as cURL
```

#### **2. Console Error Analysis**
```javascript
// Enable all log levels: Verbose, Info, Warnings, Errors
// Look for:
console.error('API Error:', error);           // Application errors
console.warn('Deprecated feature');           // Warnings
console.info('Request completed');            // Info logs
console.debug('Detailed debug info');        // Debug info (may need to enable)
```

#### **3. Application Tab Debugging**
```javascript
// Local Storage
localStorage.getItem('api-cache');
localStorage.getItem('user-preferences');

// Session Storage  
sessionStorage.getItem('current-session');

// Service Workers
navigator.serviceWorker.getRegistrations();
```

### **Performance Tab Analysis**
```javascript
// Record performance during API calls
// Look for:
// 1. Long tasks that block the main thread
// 2. Memory leaks (increasing heap size)
// 3. Excessive DOM manipulations
// 4. Slow function execution
```

## 🔧 **Common Fix Patterns**

### **Pattern 1: Retry with Exponential Backoff**
```typescript
export class RetryingOrchestratorAPI extends OrchestratorAPI {
  async makeRequestWithRetry<T>(
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
        
        // Don't retry for client errors (4xx)
        if (error.message.includes('400') || 
            error.message.includes('401') || 
            error.message.includes('403') || 
            error.message.includes('404')) {
          throw error;
        }
        
        // Wait before retry with exponential backoff
        if (attempt < maxRetries - 1) {
          const delay = Math.min(1000 * Math.pow(2, attempt), 10000);
          console.log(`Retrying request in ${delay}ms (attempt ${attempt + 1}/${maxRetries})`);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    
    throw new Error(`Request failed after ${maxRetries} attempts: ${lastError.message}`);
  }
}
```

### **Pattern 2: Graceful Degradation**
```typescript
export class RobustOrchestratorAPI extends OrchestratorAPI {
  async processMessage(query: string): Promise<ProcessResponse | null> {
    try {
      // Try primary endpoint
      return await this.makeRequest<ProcessResponse>('/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
    } catch (primaryError) {
      console.warn('Primary API failed, trying fallback:', primaryError);
      
      try {
        // Fallback to simpler endpoint
        const response = await this.makeRequest<any>('/simple-process', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ q: query }),
        });
        
        // Convert fallback response to standard format
        return {
          request_id: 'fallback-' + Date.now(),
          agent_id: 'fallback',
          agent_name: 'Fallback Agent',
          protocol: 'simple',
          content: response.text || response.message || 'Fallback response',
          confidence: 0.5,
          success: true,
          duration_ms: 0,
          timestamp: new Date().toISOString(),
        };
      } catch (fallbackError) {
        console.error('Both primary and fallback APIs failed:', {
          primary: primaryError,
          fallback: fallbackError,
        });
        
        // Return null to let UI handle the failure
        return null;
      }
    }
  }
}
```

## 🎯 **Prevention Checklist**

### **Development Phase**
- [ ] Test API endpoints with curl before frontend integration
- [ ] Verify CORS configuration for all target origins  
- [ ] Implement proper error handling for all HTTP status codes
- [ ] Add request/response logging in development mode
- [ ] Test with network throttling (slow 3G, offline)
- [ ] Validate request payloads before sending
- [ ] Handle parsing errors gracefully
- [ ] Test timeout scenarios

### **Pre-Production**
- [ ] Update API URLs for production environment
- [ ] Test HTTPS requirements and SSL certificates
- [ ] Verify Content Security Policy compatibility
- [ ] Test with production-like network conditions
- [ ] Enable error tracking (Sentry, LogRocket, etc.)
- [ ] Set up monitoring and alerts
- [ ] Test error boundaries and fallback UI

### **Production Monitoring**  
- [ ] Monitor API response times and error rates
- [ ] Track CORS errors and failed requests
- [ ] Monitor memory usage and performance metrics
- [ ] Set up alerts for high error rates
- [ ] Review logs regularly for new error patterns

## 🎯 **Key Takeaways**

1. **Always test backend independently** - Verify API works before debugging frontend
2. **Use browser dev tools systematically** - Network tab is your best friend
3. **Log everything in development** - Add detailed logging, remove in production
4. **Handle all error scenarios** - Network, parsing, timeout, and server errors
5. **Test across environments** - Development, staging, and production differences
6. **Monitor proactively** - Don't wait for users to report issues
7. **Implement graceful degradation** - Always have fallback options

---

**Next**: [03-production-deployment-issues.md](./03-production-deployment-issues.md) - Production Environment Troubleshooting

**Previous**: [01-common-streaming-issues.md](./01-common-streaming-issues.md)