# Troubleshooting: Common Streaming Issues & Solutions

## 🎯 **What You'll Learn**

This comprehensive troubleshooting guide covers:
- The most common streaming issues developers encounter
- Step-by-step debugging techniques for real-time applications
- Production-ready solutions and preventive measures
- Browser-specific compatibility issues and workarounds
- Performance troubleshooting for high-frequency streaming

## 🚨 **Quick Diagnostic Checklist**

Before diving into specific issues, run this diagnostic sequence:

### **1. Backend Health Check**
```bash
# Check if orchestrator is running and healthy
curl -s http://localhost:8004/health | jq '.'

# Expected response:
# {
#   "status": "healthy",
#   "agents_discovered": 2,
#   "timestamp": "2024-01-15T10:30:00Z"
# }
```

### **2. Streaming Endpoint Test**
```bash
# Test streaming endpoint directly
curl -N -X POST http://localhost:8004/process/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello"}' \
  --max-time 30

# Should see streaming events like:
# data: {"event": "routing_completed", "agent": "hello-world"}
# data: {"event": "response_chunk", "text": "Hello!"}
```

### **3. Browser Console Check**
```javascript
// Open browser dev tools and run:
console.log('EventSource supported:', typeof EventSource !== 'undefined');
console.log('Fetch supported:', typeof fetch !== 'undefined');
console.log('AbortController supported:', typeof AbortController !== 'undefined');

// Check for CORS errors, failed requests, or JavaScript errors
```

## 🔧 **Issue 1: EventSource Connection Fails**

### **Symptoms**
```
EventSource's response has a MIME type ('application/json') that is not 'text/event-stream'
Failed to construct 'EventSource': The URL's scheme must be either 'http' or 'https'
```

### **Root Causes & Solutions**

#### **Cause 1: Incorrect Content-Type**
The backend isn't sending proper Server-Sent Events headers.

**Solution:**
```python
# Backend fix (FastAPI/Python)
from fastapi.responses import StreamingResponse

@app.post("/process/stream")
async def stream_process(request: ProcessRequest):
    async def generate_stream():
        yield f"data: {json.dumps({'event': 'started'})}\n\n"
        # ... generate more events
        yield f"data: {json.dumps({'event': 'completed'})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",  # ← Critical!
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",  # Adjust for production
        }
    )
```

#### **Cause 2: CORS Issues**
Cross-origin requests blocked by browser security.

**Solution:**
```typescript
// Frontend workaround during development
const StreamingAPI = () => {
  private getStreamingUrl() {
    // Use proxy during development to avoid CORS
    if (process.env.NODE_ENV === 'development') {
      return '/api/process/stream';  // Proxied by Vite
    }
    return 'http://localhost:8004/process/stream';
  }
}
```

```typescript
// vite.config.ts - Add proxy configuration
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8004',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
});
```

#### **Cause 3: Invalid URL Protocol**
Using wrong protocol or malformed URLs.

**Solution:**
```typescript
class StreamingAPI {
  private buildStreamingUrl(): string {
    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
    const host = process.env.NODE_ENV === 'production' 
      ? process.env.REACT_APP_API_HOST 
      : 'localhost:8004';
    
    return `${protocol}//${host}/process/stream`;
  }
}
```

### **Debug Commands**
```bash
# Check backend CORS configuration
curl -H "Origin: http://localhost:5173" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS http://localhost:8004/process/stream

# Test with different origins
curl -H "Origin: http://localhost:3000" \
     -X POST http://localhost:8004/process/stream \
     -d '{"query": "test"}'
```

## ⏱️ **Issue 2: Stream Disconnects After 30-60 Seconds**

### **Symptoms**
- EventSource connects successfully
- Receives events for 30-60 seconds
- Then suddenly disconnects with `onerror` event
- May reconnect automatically but same pattern repeats

### **Root Causes & Solutions**

#### **Cause 1: Proxy/Load Balancer Timeout**
Nginx, Apache, or cloud load balancers have default connection timeouts.

**Solution: Backend Keepalive**
```python
import asyncio
import time

async def generate_stream():
    last_event_time = time.time()
    
    # Your actual streaming logic
    async for event in your_stream_generator():
        yield f"data: {json.dumps(event)}\n\n"
        last_event_time = time.time()
    
    # Keepalive mechanism
    while not stream_completed:
        current_time = time.time()
        
        # Send keepalive every 20 seconds if no events
        if current_time - last_event_time > 20:
            yield f"data: {json.dumps({'event': 'keepalive', 'timestamp': current_time})}\n\n"
            last_event_time = current_time
        
        await asyncio.sleep(5)
```

**Solution: Frontend Reconnection**
```typescript
class ResilientStreamingAPI extends StreamingAPI {
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second

  protected setupEventSource(url: string, callbacks: StreamingCallbacks): EventSource {
    const eventSource = new EventSource(url);
    
    eventSource.onerror = (error) => {
      console.warn('EventSource error:', error);
      
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        console.log(`Reconnecting in ${this.reconnectDelay}ms (attempt ${this.reconnectAttempts + 1})`);
        
        setTimeout(() => {
          this.reconnectAttempts++;
          this.reconnectDelay = Math.min(this.reconnectDelay * 2, 10000); // Exponential backoff
          this.setupEventSource(url, callbacks);
        }, this.reconnectDelay);
      } else {
        callbacks.onError?.('Max reconnection attempts reached');
      }
    };
    
    eventSource.onopen = () => {
      console.log('EventSource connection established');
      this.reconnectAttempts = 0; // Reset on successful connection
      this.reconnectDelay = 1000;
    };
    
    return eventSource;
  }
}
```

#### **Cause 2: Browser Tab Throttling**
Browsers throttle inactive tabs to save resources.

**Solution: Page Visibility API**
```typescript
class VisibilityAwareStreamingAPI extends StreamingAPI {
  private wasTabHidden = false;
  
  constructor() {
    super();
    this.setupVisibilityHandling();
  }
  
  private setupVisibilityHandling() {
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        console.log('Tab hidden - marking for reconnection');
        this.wasTabHidden = true;
      } else if (this.wasTabHidden) {
        console.log('Tab visible again - checking connection');
        this.wasTabHidden = false;
        this.checkAndReconnectIfNeeded();
      }
    });
  }
  
  private checkAndReconnectIfNeeded() {
    // Verify connection is still alive with a quick ping
    if (this.currentEventSource && this.currentEventSource.readyState === EventSource.CLOSED) {
      console.log('Connection lost while tab was hidden - reconnecting');
      this.reconnect();
    }
  }
}
```

## 📊 **Issue 3: Missing or Corrupted Stream Chunks**

### **Symptoms**
```javascript
// Expected:
"The answer is 42"

// Received:
"The answer" "is " "42" (as separate chunks)
// Or: "Theanswer is42" (missing spaces)
// Or: "The answer is" (missing final chunk)
```

### **Root Causes & Solutions**

#### **Cause 1: Race Conditions in Chunk Processing**
Multiple chunks arriving faster than they can be processed.

**Solution: Ordered Chunk Processing**
```typescript
class OrderedStreamingAPI extends StreamingAPI {
  private chunkBuffer = new Map<number, string>();
  private expectedSequence = 0;
  private processingQueue = new Set<number>();

  protected handleStreamEvent(event: MessageEvent, callbacks: StreamingCallbacks) {
    let eventData;
    
    try {
      eventData = JSON.parse(event.data);
    } catch (error) {
      console.error('Failed to parse stream event:', event.data);
      return;
    }

    if (eventData.event === 'response_chunk') {
      const sequence = eventData.sequence || 0;
      const text = eventData.text || '';
      
      if (sequence === this.expectedSequence) {
        // Process immediately - in order
        this.processChunk(text, callbacks);
        this.expectedSequence++;
        
        // Process any buffered chunks that are now in order
        while (this.chunkBuffer.has(this.expectedSequence)) {
          const bufferedText = this.chunkBuffer.get(this.expectedSequence)!;
          this.processChunk(bufferedText, callbacks);
          this.chunkBuffer.delete(this.expectedSequence);
          this.expectedSequence++;
        }
      } else {
        // Buffer out-of-order chunk
        console.log(`Buffering out-of-order chunk: expected ${this.expectedSequence}, got ${sequence}`);
        this.chunkBuffer.set(sequence, text);
      }
    }
  }
  
  private processChunk(text: string, callbacks: StreamingCallbacks) {
    if (text && text.trim()) {
      callbacks.onResponseChunk?.(text);
    }
  }
}
```

#### **Cause 2: Text Encoding Issues**
UTF-8 characters split across chunk boundaries.

**Solution: Proper Text Decoding**
```typescript
class TextDecodingStreamingAPI extends StreamingAPI {
  private textDecoder = new TextDecoder('utf-8', { stream: true });
  private accumulatedText = '';

  protected handleRawChunk(chunk: Uint8Array, callbacks: StreamingCallbacks) {
    // Properly decode UTF-8, handling multi-byte characters
    const decodedText = this.textDecoder.decode(chunk, { stream: true });
    this.accumulatedText += decodedText;
    
    // Process complete lines (separated by \n\n in SSE)
    const lines = this.accumulatedText.split('\n\n');
    
    // Keep the last incomplete line in buffer
    this.accumulatedText = lines.pop() || '';
    
    // Process complete lines
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.substring(6);
        this.handleDataLine(data, callbacks);
      }
    }
  }
}
```

### **Debug Commands**
```bash
# Monitor chunk delivery with timestamps
curl -N -X POST http://localhost:8004/process/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Tell me a story"}' | \
  while IFS= read -r line; do
    echo "[$(date '+%H:%M:%S.%3N')] $line"
  done
```

## 🌐 **Issue 4: Browser-Specific Problems**

### **Safari Issues**

#### **Problem**: EventSource fails silently in Safari
**Solution**:
```typescript
class SafariCompatibleStreamingAPI extends StreamingAPI {
  protected createEventSource(url: string): EventSource | null {
    try {
      // Safari requires specific configuration
      const eventSource = new EventSource(url, {
        withCredentials: false, // Safari is strict about credentials
      });
      
      // Safari sometimes needs a connection delay
      if (this.isSafari()) {
        return new Promise((resolve) => {
          setTimeout(() => resolve(eventSource), 100);
        });
      }
      
      return eventSource;
    } catch (error) {
      console.error('Safari EventSource creation failed:', error);
      
      // Fallback to fetch-based streaming for Safari
      return this.createFallbackStream(url);
    }
  }
  
  private isSafari(): boolean {
    const ua = navigator.userAgent;
    return /Safari/.test(ua) && !/Chrome|Chromium/.test(ua);
  }
  
  private async createFallbackStream(url: string) {
    // Implement fetch-based streaming for Safari
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    
    const reader = response.body?.getReader();
    if (!reader) throw new Error('ReadableStream not supported');
    
    // Manually process stream chunks
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = new TextDecoder().decode(value);
      this.processManualChunk(chunk);
    }
  }
}
```

### **Firefox Issues**

#### **Problem**: EventSource disconnects on large responses
**Solution**:
```typescript
// Firefox has stricter memory limits for EventSource
class FirefoxOptimizedStreamingAPI extends StreamingAPI {
  private chunkCount = 0;
  private readonly FIREFOX_CHUNK_LIMIT = 1000;
  
  protected handleStreamEvent(event: MessageEvent, callbacks: StreamingCallbacks) {
    this.chunkCount++;
    
    // Restart connection before hitting Firefox's internal limits
    if (this.isFirefox() && this.chunkCount > this.FIREFOX_CHUNK_LIMIT) {
      console.log('Restarting EventSource to prevent Firefox memory issues');
      this.restartConnection();
      return;
    }
    
    super.handleStreamEvent(event, callbacks);
  }
  
  private isFirefox(): boolean {
    return navigator.userAgent.includes('Firefox');
  }
  
  private restartConnection() {
    if (this.currentEventSource) {
      this.currentEventSource.close();
      // Recreate connection with current context
      this.reconnect();
      this.chunkCount = 0;
    }
  }
}
```

### **Chrome Issues**

#### **Problem**: Memory leaks with long-running streams
**Solution**:
```typescript
class MemoryEfficientStreamingAPI extends StreamingAPI {
  private memoryMonitorInterval: number | null = null;
  private readonly MEMORY_CHECK_INTERVAL = 30000; // 30 seconds
  
  constructor() {
    super();
    this.startMemoryMonitoring();
  }
  
  private startMemoryMonitoring() {
    if ('memory' in performance) {
      this.memoryMonitorInterval = window.setInterval(() => {
        const memory = (performance as any).memory;
        const usedMB = memory.usedJSHeapSize / 1024 / 1024;
        
        console.log(`Memory usage: ${usedMB.toFixed(1)} MB`);
        
        // Restart connection if memory usage is excessive
        if (usedMB > 100) { // 100MB threshold
          console.warn('High memory usage detected - restarting connection');
          this.cleanupAndRestart();
        }
      }, this.MEMORY_CHECK_INTERVAL);
    }
  }
  
  private cleanupAndRestart() {
    // Clear any accumulated data
    this.clearAccumulatedData();
    
    // Restart connection
    this.restartConnection();
    
    // Force garbage collection if available
    if ('gc' in window) {
      (window as any).gc();
    }
  }
  
  destroy() {
    super.destroy();
    if (this.memoryMonitorInterval) {
      clearInterval(this.memoryMonitorInterval);
    }
  }
}
```

## 🔍 **Issue 5: Performance Problems**

### **Symptoms**
- UI becomes sluggish during streaming
- High CPU usage in browser
- Delayed response to user interactions
- Browser tab becomes unresponsive

### **Solutions**

#### **Solution 1: Throttle UI Updates**
```typescript
class PerformanceOptimizedStreamingAPI extends StreamingAPI {
  private updateThrottle: number | null = null;
  private pendingUpdate = '';
  private readonly UPDATE_INTERVAL = 50; // 20 FPS
  
  protected handleStreamEvent(event: MessageEvent, callbacks: StreamingCallbacks) {
    if (event.data.includes('response_chunk')) {
      const eventData = JSON.parse(event.data);
      this.pendingUpdate += eventData.text || '';
      
      // Throttle UI updates to prevent overwhelming the browser
      if (!this.updateThrottle) {
        this.updateThrottle = window.setTimeout(() => {
          if (this.pendingUpdate) {
            callbacks.onResponseChunk?.(this.pendingUpdate);
            this.pendingUpdate = '';
          }
          this.updateThrottle = null;
        }, this.UPDATE_INTERVAL);
      }
    } else {
      // Non-chunk events process immediately
      super.handleStreamEvent(event, callbacks);
    }
  }
}
```

#### **Solution 2: Use Web Workers for Heavy Processing**
```typescript
// worker.ts
self.addEventListener('message', (event) => {
  const { type, data } = event.data;
  
  if (type === 'PROCESS_CHUNKS') {
    // Heavy processing in worker thread
    const processed = data.chunks.map(chunk => ({
      ...chunk,
      processedContent: processContent(chunk.content),
      timestamp: Date.now(),
    }));
    
    self.postMessage({ type: 'CHUNKS_PROCESSED', data: processed });
  }
});

// Main thread
class WorkerStreamingAPI extends StreamingAPI {
  private worker: Worker;
  private chunkQueue: string[] = [];
  
  constructor() {
    super();
    this.worker = new Worker(new URL('./streaming-worker.ts', import.meta.url));
    this.worker.onmessage = this.handleWorkerMessage.bind(this);
  }
  
  protected handleStreamEvent(event: MessageEvent, callbacks: StreamingCallbacks) {
    if (event.data.includes('response_chunk')) {
      // Queue chunks for worker processing
      const eventData = JSON.parse(event.data);
      this.chunkQueue.push(eventData.text);
      
      // Process in batches
      if (this.chunkQueue.length >= 10) {
        this.worker.postMessage({
          type: 'PROCESS_CHUNKS',
          data: { chunks: this.chunkQueue },
        });
        this.chunkQueue = [];
      }
    }
  }
}
```

### **Debug Tools**
```javascript
// Monitor performance in browser console
const perfMonitor = {
  start() {
    this.startTime = performance.now();
    this.frameCount = 0;
    
    const measureFrame = () => {
      this.frameCount++;
      if (this.frameCount % 60 === 0) { // Every 60 frames
        const fps = 60 / ((performance.now() - this.lastFrameTime) / 1000);
        console.log(`FPS: ${fps.toFixed(1)}`);
        this.lastFrameTime = performance.now();
      }
      requestAnimationFrame(measureFrame);
    };
    
    this.lastFrameTime = performance.now();
    requestAnimationFrame(measureFrame);
  }
};

// Usage
perfMonitor.start();
```

## 🛠️ **Issue 6: Development vs Production Differences**

### **Common Environment Issues**

#### **HTTPS Requirements**
```typescript
class ProductionStreamingAPI extends StreamingAPI {
  private getProtocol(): string {
    // Production often requires HTTPS
    if (window.location.protocol === 'https:') {
      return 'https:';
    }
    
    // Development might use HTTP
    if (process.env.NODE_ENV === 'development') {
      return 'http:';
    }
    
    // Default to current page protocol
    return window.location.protocol;
  }
  
  protected buildStreamingUrl(): string {
    const protocol = this.getProtocol();
    const host = process.env.NODE_ENV === 'production'
      ? process.env.REACT_APP_API_HOST
      : 'localhost:8004';
    
    return `${protocol}//${host}/process/stream`;
  }
}
```

#### **Content Security Policy**
```html
<!-- Add to index.html for production -->
<meta http-equiv="Content-Security-Policy" content="
  connect-src 'self' wss: ws: https://your-api-domain.com;
  default-src 'self';
">
```

## 🎯 **Prevention Best Practices**

### **1. Implement Circuit Breakers**
```typescript
class CircuitBreakerStreamingAPI extends StreamingAPI {
  private failureCount = 0;
  private lastFailureTime = 0;
  private readonly FAILURE_THRESHOLD = 5;
  private readonly RECOVERY_TIMEOUT = 30000; // 30 seconds
  
  async processMessageStream(query: string, callbacks: StreamingCallbacks): Promise<void> {
    if (this.isCircuitOpen()) {
      throw new Error('Circuit breaker is open - streaming temporarily disabled');
    }
    
    try {
      await super.processMessageStream(query, callbacks);
      this.onSuccess();
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }
  
  private isCircuitOpen(): boolean {
    if (this.failureCount < this.FAILURE_THRESHOLD) {
      return false;
    }
    
    const timeSinceLastFailure = Date.now() - this.lastFailureTime;
    return timeSinceLastFailure < this.RECOVERY_TIMEOUT;
  }
  
  private onSuccess() {
    this.failureCount = 0;
  }
  
  private onFailure() {
    this.failureCount++;
    this.lastFailureTime = Date.now();
  }
}
```

### **2. Add Comprehensive Logging**
```typescript
class LoggingStreamingAPI extends StreamingAPI {
  private logger = {
    debug: (message: string, data?: any) => {
      if (process.env.NODE_ENV === 'development') {
        console.log(`[StreamingAPI] ${message}`, data);
      }
    },
    warn: (message: string, data?: any) => {
      console.warn(`[StreamingAPI] ${message}`, data);
    },
    error: (message: string, error: any) => {
      console.error(`[StreamingAPI] ${message}`, error);
      
      // Send to error tracking service in production
      if (process.env.NODE_ENV === 'production' && window.Sentry) {
        window.Sentry.captureException(error, {
          tags: { component: 'StreamingAPI' },
          extra: { message, timestamp: Date.now() }
        });
      }
    }
  };
  
  protected handleStreamEvent(event: MessageEvent, callbacks: StreamingCallbacks) {
    this.logger.debug('Stream event received', { 
      type: event.type, 
      data: event.data?.substring(0, 100) + '...' 
    });
    
    try {
      super.handleStreamEvent(event, callbacks);
    } catch (error) {
      this.logger.error('Failed to handle stream event', error);
      throw error;
    }
  }
}
```

## 🎯 **Key Takeaways**

1. **Always implement reconnection logic** - Networks are unreliable
2. **Handle browser differences** - Test in Safari, Firefox, and Chrome
3. **Monitor performance actively** - Use throttling and Web Workers when needed
4. **Plan for production differences** - HTTPS, CSP, and proxy configurations
5. **Log comprehensively** - Debug information is crucial for production issues
6. **Use circuit breakers** - Prevent cascade failures
7. **Test with real network conditions** - Throttling, high latency, intermittent connectivity

---

**Next**: [02-api-integration-debugging.md](./02-api-integration-debugging.md) - Debugging API Integration Issues

**Previous**: [Advanced Features](../advanced-features/03-troubleshooting-streaming-api.md)