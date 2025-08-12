# Advanced Troubleshooting: Streaming & API Integration

## 🎯 **What You'll Learn**

This comprehensive troubleshooting guide covers:
- Common streaming and API integration issues and their solutions
- Debugging techniques for real-time applications
- Network troubleshooting and connection management
- Protocol-specific parsing problems
- Production deployment issues and monitoring

## 🚨 **Quick Diagnostic Checklist**

**Before diving into specific issues, run this quick diagnostic:**

```bash
# 1. Check if orchestrator is running
curl http://localhost:8004/health

# 2. Check if agents are discovered
curl http://localhost:8004/agents

# 3. Test regular API endpoint
curl -X POST http://localhost:8004/process \
  -H "Content-Type: application/json" \
  -d '{"query": "hello"}'

# 4. Test streaming endpoint (should start streaming)
curl -X POST http://localhost:8004/process/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "hello"}'
```

**Frontend Quick Check:**
```javascript
// Open browser console and run:
console.log('EventSource supported:', typeof EventSource !== 'undefined');
console.log('Fetch supported:', typeof fetch !== 'undefined');
console.log('Local storage working:', localStorage.setItem('test', '1') || localStorage.getItem('test') === '1');
```

## 🔧 **Streaming Issues**

### **Issue 1: "EventSource failed to connect"**

**Symptoms:**
```
EventSource's response has a MIME type ('application/json') that is not 'text/plain' or 'text/event-stream'
```

**Root Cause:** Backend not sending correct Content-Type headers for SSE.

**Solution:**
```python
# Backend fix (FastAPI)
from fastapi.responses import StreamingResponse

@app.post("/process/stream")
async def stream_response():
    async def generate_events():
        yield f"data: {json.dumps({'event': 'started'})}\n\n"
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",  # ← Correct MIME type
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

**Frontend Workaround:**
```typescript
// If you can't fix backend immediately
const streamingApi = new StreamingAPI();

// Override the connection method temporarily
(streamingApi as any).handleStreamingEvents = async function(url, callbacks) {
  // Use fetch with streaming instead of EventSource
  const response = await fetch(url, { method: 'POST' });
  const reader = response.body?.getReader();
  
  while (true) {
    const { done, value } = await reader!.read();
    if (done) break;
    
    // Process streaming data manually
    const chunk = new TextDecoder().decode(value);
    // Parse and handle events...
  }
};
```

### **Issue 2: "Connection drops after 30 seconds"**

**Symptoms:**
- EventSource connects successfully
- Receives events for ~30 seconds
- Then suddenly disconnects

**Root Cause:** Proxy timeout (nginx, load balancer, etc.)

**Solution 1: Backend keepalive**
```python
# Send periodic keepalive events
async def generate_events():
    last_event_time = time.time()
    
    async for real_event in process_stream():
        yield f"data: {json.dumps(real_event)}\n\n"
        last_event_time = time.time()
    
    # Send keepalive if no events for 20 seconds
    while True:
        if time.time() - last_event_time > 20:
            yield f"data: {json.dumps({'event': 'keepalive'})}\n\n"
            last_event_time = time.time()
        
        await asyncio.sleep(5)
```

**Solution 2: Frontend reconnection**
```typescript
class StreamingAPI {
  private reconnectDelay = 5000;
  private maxReconnectAttempts = 5;
  
  private setupEventSource(url: string, callbacks: StreamingCallbacks) {
    const eventSource = new EventSource(url);
    
    eventSource.onerror = (error) => {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        console.log(`Reconnecting in ${this.reconnectDelay}ms...`);
        setTimeout(() => {
          this.setupEventSource(url, callbacks);
        }, this.reconnectDelay);
        this.reconnectAttempts++;
      }
    };
  }
}
```

### **Issue 3: "Events arriving out of order"**

**Symptoms:**
```
StreamingAPI: Received chunk: "answer is"
StreamingAPI: Received chunk: "The "  
StreamingAPI: Received chunk: "4"
// Should be: "The answer is 4"
```

**Root Cause:** Network buffering or processing delays.

**Solution: Sequence numbering**
```typescript
interface SequencedEvent {
  event: string;
  sequence: number;
  data: any;
}

class StreamingAPI {
  private eventBuffer = new Map<number, SequencedEvent>();
  private expectedSequence = 0;
  
  private handleStreamEvent(event: MessageEvent, callbacks: StreamingCallbacks) {
    const eventData: SequencedEvent = JSON.parse(event.data);
    
    if (eventData.sequence === this.expectedSequence) {
      // Process immediately
      this.processEvent(eventData, callbacks);
      this.expectedSequence++;
      
      // Process any buffered events that are now in order
      while (this.eventBuffer.has(this.expectedSequence)) {
        const bufferedEvent = this.eventBuffer.get(this.expectedSequence)!;
        this.processEvent(bufferedEvent, callbacks);
        this.eventBuffer.delete(this.expectedSequence);
        this.expectedSequence++;
      }
    } else {
      // Buffer out-of-order event
      this.eventBuffer.set(eventData.sequence, eventData);
    }
  }
}
```

### **Issue 4: "Streaming stops working in Safari"**

**Symptoms:**
- Works fine in Chrome/Firefox
- Safari shows "EventSource failed" errors
- No obvious backend errors

**Root Cause:** Safari has stricter CORS and EventSource limitations.

**Solution:**
```typescript
// Safari-specific EventSource handling
class SafariCompatibleStreamingAPI extends StreamingAPI {
  private createEventSource(url: string): EventSource {
    // Safari requires explicit CORS headers
    const eventSource = new EventSource(url, {
      withCredentials: false // Safari can be picky about credentials
    });
    
    // Safari sometimes needs a delay before connection
    if (this.isSafari()) {
      return new Promise((resolve) => {
        setTimeout(() => resolve(eventSource), 100);
      });
    }
    
    return eventSource;
  }
  
  private isSafari(): boolean {
    return /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
  }
}
```

**Backend CORS fix:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=False,  # Set to False for EventSource compatibility
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## 🌐 **API Integration Issues**

### **Issue 5: "API calls work in Postman but fail in browser"**

**Symptoms:**
```
TypeError: Failed to fetch
CORS policy: No 'Access-Control-Allow-Origin' header is present
```

**Root Cause:** CORS misconfiguration.

**Quick Fix:**
```typescript
// Temporary development workaround
const apiService = new OrchestratorAPI();

// Override fetch with proxy during development
if (process.env.NODE_ENV === 'development') {
  apiService.baseUrl = '/api'; // Proxy to avoid CORS
}
```

**Vite Proxy Configuration:**
```typescript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8004',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
});
```

### **Issue 6: "Requests timeout after exactly 30 seconds"**

**Symptoms:**
- API calls work for simple queries
- Complex queries always timeout at 30 seconds
- Backend logs show request is still processing

**Root Cause:** Default fetch timeout.

**Solution:**
```typescript
class OrchestratorAPI {
  private async makeRequest<T>(endpoint: string, options: RequestInit = {}) {
    // Increase timeout for complex operations
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minutes
    
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      return response;
      
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error.name === 'AbortError') {
        throw new Error('Request timeout - the operation is taking longer than expected');
      }
      
      throw error;
    }
  }
}
```

### **Issue 7: "Response data is undefined but status is 200"**

**Symptoms:**
```typescript
const response = await orchestratorApi.processMessage("hello");
console.log(response); // undefined
// But network tab shows 200 OK with valid JSON
```

**Root Cause:** JSON parsing or response structure issues.

**Debug Solution:**
```typescript
class OrchestratorAPI {
  private async makeRequest<T>(endpoint: string, options: RequestInit = {}) {
    const response = await fetch(`${this.baseUrl}${endpoint}`, options);
    
    // Debug logging
    console.log('Response status:', response.status);
    console.log('Response headers:', response.headers);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    // Check content type
    const contentType = response.headers.get('content-type');
    if (!contentType?.includes('application/json')) {
      const text = await response.text();
      console.error('Expected JSON, got:', contentType, text);
      throw new Error('Server returned non-JSON response');
    }
    
    try {
      const data = await response.json();
      console.log('Parsed data:', data);
      return data;
    } catch (parseError) {
      const text = await response.text();
      console.error('JSON parse failed:', parseError, 'Raw response:', text);
      throw new Error('Failed to parse server response as JSON');
    }
  }
}
```

## 🔍 **Protocol Parsing Issues**

### **Issue 8: "A2A responses show raw JSON instead of text"**

**Symptoms:**
```
Message displays: {"raw_response":{"parts":[{"kind":"text","text":"Hello"}]}}
Should display: Hello
```

**Root Cause:** Protocol parsing not working correctly.

**Solution:**
```typescript
class OrchestratorAPI {
  public extractResponseContent(data: any): string {
    console.log('Extracting content from:', data); // Debug log
    
    const responseData = data.response_data;
    const protocol = data.protocol?.toLowerCase();
    
    // A2A Protocol debugging
    if (protocol === 'a2a') {
      console.log('A2A response data:', responseData);
      
      if (!responseData?.raw_response?.parts) {
        console.warn('A2A response missing expected structure');
        return this.tryFallbackExtraction(data);
      }
      
      const textParts = responseData.raw_response.parts
        .filter((part: any) => {
          console.log('Processing part:', part);
          return part.kind === 'text' || !part.kind;
        })
        .map((part: any) => part.text)
        .filter(Boolean);
      
      console.log('Extracted text parts:', textParts);
      
      if (textParts.length > 0) {
        return textParts.join(' ').trim();
      }
    }
    
    // Fallback extraction
    return this.tryFallbackExtraction(data);
  }
  
  private tryFallbackExtraction(data: any): string {
    // Try various common formats
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
        console.log('Found content via fallback:', candidate);
        return candidate.trim();
      }
    }
    
    console.warn('No extractable content found, returning JSON');
    return JSON.stringify(data, null, 2);
  }
}
```

### **Issue 9: "ACP responses not displaying correctly"**

**Symptoms:**
- A2A responses work fine
- ACP responses show "No response content available"
- Backend logs show ACP agent returning data

**Root Cause:** ACP protocol parsing missing or incorrect.

**Solution:**
```typescript
public extractResponseContent(data: any): string {
  const responseData = data.response_data;
  const protocol = data.protocol?.toLowerCase();
  
  // Enhanced ACP Protocol handling
  if (protocol === 'acp') {
    console.log('ACP response data:', responseData);
    
    // Try multiple ACP response formats
    const acpCandidates = [
      responseData?.content,
      responseData?.response,
      responseData?.output,
      responseData?.result,
      responseData?.data,
    ];
    
    for (const candidate of acpCandidates) {
      if (typeof candidate === 'string' && candidate.trim()) {
        return candidate.trim();
      }
      
      // Handle nested structures
      if (typeof candidate === 'object' && candidate?.text) {
        return candidate.text;
      }
    }
    
    // ACP might return array of content
    if (Array.isArray(responseData?.content)) {
      return responseData.content
        .filter(item => typeof item === 'string')
        .join(' ')
        .trim();
    }
  }
  
  // Continue with A2A and fallback logic...
}
```

## ⚡ **Performance Issues**

### **Issue 10: "Chat becomes slow with many messages"**

**Symptoms:**
- First few messages are fast
- App slows down after 50+ messages
- Browser tab starts using high CPU

**Root Cause:** React re-rendering entire message list on every update.

**Solution: Virtual scrolling**
```typescript
import { FixedSizeList as List } from 'react-window';

const VirtualizedMessageList: React.FC<{ messages: Message[] }> = ({ messages }) => {
  const Row = ({ index, style }: { index: number, style: React.CSSProperties }) => (
    <div style={style}>
      <Message message={messages[index]} />
    </div>
  );
  
  return (
    <List
      height={600} // Fixed height
      itemCount={messages.length}
      itemSize={100} // Estimated message height
      width="100%"
    >
      {Row}
    </List>
  );
};
```

**Solution: Message pagination**
```typescript
const PaginatedMessageList: React.FC<{ messages: Message[] }> = ({ messages }) => {
  const [visibleCount, setVisibleCount] = useState(50);
  
  const visibleMessages = useMemo(() => {
    // Show last N messages
    return messages.slice(-visibleCount);
  }, [messages, visibleCount]);
  
  const loadMore = () => {
    setVisibleCount(prev => Math.min(prev + 50, messages.length));
  };
  
  return (
    <div>
      {messages.length > visibleCount && (
        <button onClick={loadMore}>
          Load {Math.min(50, messages.length - visibleCount)} more messages
        </button>
      )}
      
      {visibleMessages.map(message => (
        <Message key={message.id} message={message} />
      ))}
    </div>
  );
};
```

### **Issue 11: "Memory usage keeps growing during long sessions"**

**Symptoms:**
- Browser memory usage increases over time
- Chat becomes unresponsive after hours of use
- DevTools show growing heap size

**Root Cause:** Memory leaks in streaming connections or message storage.

**Solution: Cleanup and limits**
```typescript
const StreamingChatContainer: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const maxMessages = 1000; // Limit message history
  
  // Cleanup old messages periodically
  useEffect(() => {
    if (messages.length > maxMessages) {
      setMessages(prev => prev.slice(-maxMessages));
      
      // Clean up localStorage too
      const recentMessages = messages.slice(-maxMessages);
      localStorage.setItem('chat-messages', JSON.stringify(recentMessages));
    }
  }, [messages.length]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Cleanup any streaming connections
      streamingApi.abort();
      
      // Clear any timers or intervals
      // Clear any event listeners
    };
  }, []);
};
```

**Solution: EventSource cleanup**
```typescript
class StreamingAPI {
  private cleanupConnections() {
    // Close EventSource
    if (this.currentEventSource) {
      this.currentEventSource.close();
      this.currentEventSource = null;
    }
    
    // Cancel any pending timeouts
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    // Clear any cached data
    this.eventBuffer.clear();
    this.messageQueue.length = 0;
  }
  
  // Call this when component unmounts
  destroy() {
    this.cleanupConnections();
  }
}
```

## 🚀 **Production Issues**

### **Issue 12: "Works in development but fails in production"**

**Common Causes and Solutions:**

**1. Environment Variables:**
```typescript
// .env.development
REACT_APP_API_URL=http://localhost:8004

// .env.production  
REACT_APP_API_URL=https://api.yourdomain.com

// Use in code:
const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8004';
```

**2. HTTPS/WSS Requirements:**
```typescript
class StreamingAPI {
  constructor() {
    // Use secure protocols in production
    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
    this.baseUrl = `${protocol}//your-api-domain.com`;
  }
}
```

**3. Content Security Policy:**
```html
<!-- Add to index.html for EventSource support -->
<meta http-equiv="Content-Security-Policy" content="
  connect-src 'self' https://your-api-domain.com;
  default-src 'self';
">
```

### **Issue 13: "High error rates in production logs"**

**Symptoms:**
- Development works fine
- Production shows many API errors
- Users report intermittent failures

**Solution: Enhanced error tracking**
```typescript
class MonitoredStreamingAPI extends StreamingAPI {
  private errorMetrics = {
    connectionFailures: 0,
    parseFailures: 0,
    timeouts: 0,
  };
  
  private trackError(errorType: string, error: Error, context?: any) {
    // Increment metrics
    this.errorMetrics[errorType]++;
    
    // Send to monitoring service
    if (window.gtag) {
      window.gtag('event', 'api_error', {
        error_type: errorType,
        error_message: error.message,
        user_agent: navigator.userAgent,
        timestamp: Date.now(),
      });
    }
    
    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error(`StreamingAPI ${errorType}:`, error, context);
    }
  }
  
  async processMessageStream(query: string, callbacks: StreamingCallbacks) {
    try {
      await super.processMessageStream(query, callbacks);
    } catch (error) {
      this.trackError('streamingFailure', error, { query });
      throw error;
    }
  }
}
```

## 🔧 **Debug Tools and Techniques**

### **Browser DevTools Investigation**

**1. Network Tab Analysis:**
```javascript
// Check for failed requests
// Look for CORS errors
// Verify request/response headers
// Check timing (slow responses = backend issue)
```

**2. Console Debugging:**
```typescript
// Add to streamingApi.ts for debugging
class DebuggingStreamingAPI extends StreamingAPI {
  private debug = process.env.NODE_ENV === 'development';
  
  private log(message: string, ...args: any[]) {
    if (this.debug) {
      console.log(`[StreamingAPI] ${message}`, ...args);
    }
  }
  
  private handleStreamEvent(event: MessageEvent, callbacks: StreamingCallbacks) {
    this.log('Received event:', event.data);
    
    try {
      const eventData = JSON.parse(event.data);
      this.log('Parsed event:', eventData);
      
      super.handleStreamEvent(event, callbacks);
    } catch (error) {
      this.log('Parse error:', error, 'Raw data:', event.data);
      throw error;
    }
  }
}
```

**3. Application Tab Investigation:**
```javascript
// Check localStorage
localStorage.getItem('chat-messages');

// Check EventSource connections
// Look at Application > Service Workers > EventSource connections
```

### **Backend Health Verification**

```bash
# Check orchestrator health
curl -v http://localhost:8004/health

# Check specific agent
curl -v http://localhost:8004/agents

# Test streaming manually
curl -N -v -X POST http://localhost:8004/process/stream \
  -H "Content-Type: application/json" \
  -d '{"query":"hello"}'

# Check logs
docker-compose logs -f orchestrator
```

### **Network-Level Debugging**

```bash
# Check if port is accessible
telnet localhost 8004

# Check for firewall issues
netstat -an | grep 8004

# DNS resolution (for production)
nslookup api.yourdomain.com
```

## 📋 **Production Monitoring Setup**

### **Error Tracking Service Integration**

```typescript
// Sentry integration example
import * as Sentry from '@sentry/react';

class ProductionStreamingAPI extends StreamingAPI {
  private captureError(error: Error, context: any) {
    Sentry.captureException(error, {
      tags: {
        component: 'StreamingAPI',
        operation: context.operation,
      },
      extra: {
        context,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString(),
      },
    });
  }
  
  async processMessageStream(query: string, callbacks: StreamingCallbacks) {
    try {
      await super.processMessageStream(query, callbacks);
    } catch (error) {
      this.captureError(error, { operation: 'processMessageStream', query });
      throw error;
    }
  }
}
```

### **Performance Monitoring**

```typescript
class PerformanceMonitoredAPI extends StreamingAPI {
  async processMessageStream(query: string, callbacks: StreamingCallbacks) {
    const startTime = performance.now();
    
    try {
      await super.processMessageStream(query, callbacks);
      
      const duration = performance.now() - startTime;
      this.trackPerformance('streaming_success', duration);
      
    } catch (error) {
      const duration = performance.now() - startTime;
      this.trackPerformance('streaming_failure', duration);
      throw error;
    }
  }
  
  private trackPerformance(event: string, duration: number) {
    // Send to analytics
    if (window.gtag) {
      window.gtag('event', event, {
        custom_parameter_duration: Math.round(duration),
      });
    }
  }
}
```

## 🎯 **Prevention Checklist**

### **Before Deployment:**
- [ ] Test with real network conditions (throttled, intermittent)
- [ ] Test with large message histories (100+ messages)
- [ ] Test all error scenarios (backend down, malformed responses)
- [ ] Verify CORS configuration for production domain
- [ ] Test in all target browsers (Chrome, Firefox, Safari)
- [ ] Check mobile compatibility
- [ ] Verify HTTPS/SSL configuration
- [ ] Set up error monitoring and alerts

### **Code Quality Checks:**
- [ ] All async operations have error handling
- [ ] EventSource connections are properly cleaned up
- [ ] Memory usage is bounded (message limits, cleanup)
- [ ] Protocol parsing has fallback logic
- [ ] Loading states are informative
- [ ] Error messages are user-friendly
- [ ] Debug logging can be easily enabled/disabled

---

**Remember:** Most production issues are network-related, not code bugs. Always check connectivity, CORS, SSL, and proxy configuration first!

---

**Next**: [Phase 4 Tutorials](../phase-4-advanced/01-agent-management-ui.md) - Agent Management Interface

**Previous**: [Message Actions System](./02-message-actions-system.md)