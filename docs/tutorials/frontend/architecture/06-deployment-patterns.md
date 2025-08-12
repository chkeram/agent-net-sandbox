# Architecture 6: Deployment Patterns - Production Deployment Strategies

## 🎯 **Learning Objectives**

By the end of this tutorial, you will understand:
- Production deployment strategies for streaming React applications
- Container orchestration patterns for multi-agent systems
- Load balancing and scaling considerations for real-time features
- Monitoring and observability for production deployments
- Security hardening for multi-protocol agent environments
- CI/CD pipeline design for complex frontend applications

## 🚀 **The Deployment Challenge**

Production deployments for streaming applications have unique challenges:
- **Real-time Requirements**: WebSocket and SSE connections need special handling
- **Multi-Agent Coordination**: Multiple services must be orchestrated together
- **State Management**: Persistent conversations across deployments
- **Performance Monitoring**: Track streaming performance and memory usage
- **Security**: Multi-protocol communications require robust security
- **Scalability**: Handle concurrent users and agent interactions

**Our goal**: Build **production-ready deployment patterns** that ensure reliability and performance at scale.

## 🏗️ **Deployment Architecture Overview**

### **Multi-Tier Deployment Strategy**

```
┌─────────────────────────────────────────────┐
│              CDN + Load Balancer            │ ← Global edge distribution
├─────────────────────────────────────────────┤
│            Frontend Application             │ ← React SPA with streaming
├─────────────────────────────────────────────┤
│             API Gateway                     │ ← Request routing & auth
├─────────────────────────────────────────────┤
│           Orchestrator Service              │ ← AI-powered agent routing
├─────────────────────────────────────────────┤  
│         Multi-Protocol Agents               │ ← A2A, ACP, MCP agents
├─────────────────────────────────────────────┤
│      Storage & Message Persistence          │ ← Database and caching
└─────────────────────────────────────────────┘
```

## 📦 **Containerization Strategies**

### **Pattern 1: Multi-Stage Docker Build**

```dockerfile
# Dockerfile.frontend - Optimized React build
FROM node:18-alpine AS base
WORKDIR /app

# Install dependencies (cached layer)
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Development dependencies for building
FROM base AS build-deps
RUN npm ci && npm cache clean --force

# Build stage
FROM build-deps AS build
COPY . .

# Build optimizations for production
ENV NODE_ENV=production
ENV GENERATE_SOURCEMAP=false
ENV INLINE_RUNTIME_CHUNK=false

# Build with performance optimizations
RUN npm run build

# Analyze bundle (optional)
RUN npm run analyze --silent > bundle-analysis.txt || true

# Production stage with nginx
FROM nginx:alpine AS production

# Security hardening
RUN adduser -D -s /bin/sh nginx-user && \
    chown -R nginx-user:nginx-user /var/cache/nginx && \
    chown -R nginx-user:nginx-user /var/log/nginx && \
    chown -R nginx-user:nginx-user /etc/nginx/conf.d
    
# Custom nginx config for SPA
COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/build /usr/share/nginx/html

# Add health check
COPY health-check.sh /health-check.sh
RUN chmod +x /health-check.sh
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /health-check.sh

USER nginx-user
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
```

```nginx
# nginx.conf - Optimized for SPA with streaming support
user nginx-user;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /tmp/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    # Basic settings
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                   '$status $body_bytes_sent "$http_referer" '
                   '"$http_user_agent" "$http_x_forwarded_for" '
                   'rt=$request_time ut=$upstream_response_time';
    
    access_log /var/log/nginx/access.log main;
    
    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 16M;
    
    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private must-revalidate;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
    
    # Upstream for API
    upstream orchestrator_api {
        server orchestrator:8004 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }
    
    upstream websocket_api {
        server orchestrator:8004 max_fails=3 fail_timeout=30s;
        keepalive 16;
    }
    
    server {
        listen 8080;
        server_name _;
        root /usr/share/nginx/html;
        index index.html;
        
        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
        
        # API proxy with streaming support
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://orchestrator_api/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Streaming optimizations
            proxy_cache off;
            proxy_buffering off;
            proxy_read_timeout 24h;
            proxy_send_timeout 24h;
            
            # Handle SSE
            proxy_set_header Cache-Control "no-cache";
            proxy_set_header Connection "";
            chunked_transfer_encoding off;
        }
        
        # WebSocket proxy
        location /ws/ {
            proxy_pass http://websocket_api/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "Upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket timeouts
            proxy_read_timeout 86400;
            proxy_send_timeout 86400;
        }
        
        # Static assets with aggressive caching
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            try_files $uri =404;
        }
        
        # SPA routing - serve index.html for all routes
        location / {
            try_files $uri $uri/ /index.html;
            
            # Security headers for HTML
            add_header X-Frame-Options "DENY" always;
            add_header X-Content-Type-Options "nosniff" always;
        }
        
        # Deny access to sensitive files
        location ~ /\. {
            deny all;
        }
        
        # Custom error pages
        error_page 404 /404.html;
        error_page 500 502 503 504 /50x.html;
        
        location = /50x.html {
            root /usr/share/nginx/html;
        }
    }
}
```

### **Pattern 2: Docker Compose for Development**

```yaml
# docker-compose.yml - Complete development environment
version: '3.8'

services:
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
      target: development
    ports:
      - "3000:3000"
    volumes:
      - .:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
      - REACT_APP_API_URL=http://localhost:8004
      - REACT_APP_WS_URL=ws://localhost:8004
      - CHOKIDAR_USEPOLLING=true
    depends_on:
      - orchestrator
      - redis
    networks:
      - agent-network

  orchestrator:
    build:
      context: ./agents/orchestrator
      dockerfile: Dockerfile
    ports:
      - "8004:8004"
    environment:
      - PYTHONPATH=/app
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/agent_network
    volumes:
      - ./agents/orchestrator:/app
    depends_on:
      - redis
      - postgres
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 40s
    networks:
      - agent-network

  a2a-math-agent:
    build:
      context: ./agents/a2a-math-agent
      dockerfile: Dockerfile
    ports:
      - "8002:8002"
    environment:
      - PYTHONPATH=/app
      - LLM_PROVIDER=openai
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./agents/a2a-math-agent:/app
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/.well-known/agent-card"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - agent-network

  acp-hello-world:
    build:
      context: ./agents/acp-hello-world
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - PYTHONPATH=/app
    volumes:
      - ./agents/acp-hello-world:/app
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - agent-network

  nginx:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/html:/usr/share/nginx/html
    depends_on:
      - frontend
      - orchestrator
    networks:
      - agent-network

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    networks:
      - agent-network

  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=agent_network
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - agent-network

  # Monitoring stack
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    networks:
      - agent-network

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    networks:
      - agent-network

volumes:
  redis-data:
  postgres-data:
  prometheus-data:
  grafana-data:

networks:
  agent-network:
    driver: bridge
```

## ☁️ **Production Kubernetes Deployment**

### **Pattern 3: Kubernetes Manifests**

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: agent-network-prod
  labels:
    name: agent-network-prod

---
# k8s/frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: agent-network-prod
  labels:
    app: frontend
    version: v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
      version: v1
  template:
    metadata:
      labels:
        app: frontend
        version: v1
    spec:
      containers:
      - name: frontend
        image: agent-network/frontend:latest
        ports:
        - containerPort: 8080
        env:
        - name: NODE_ENV
          value: "production"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        securityContext:
          allowPrivilegeEscalation: false
          runAsNonRoot: true
          runAsUser: 101
          capabilities:
            drop:
            - ALL

---
# k8s/frontend-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: agent-network-prod
spec:
  selector:
    app: frontend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP

---
# k8s/frontend-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: frontend-hpa
  namespace: agent-network-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: frontend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80

---
# k8s/orchestrator-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orchestrator
  namespace: agent-network-prod
  labels:
    app: orchestrator
    version: v1
spec:
  replicas: 2
  selector:
    matchLabels:
      app: orchestrator
      version: v1
  template:
    metadata:
      labels:
        app: orchestrator
        version: v1
    spec:
      containers:
      - name: orchestrator
        image: agent-network/orchestrator:latest
        ports:
        - containerPort: 8004
        env:
        - name: PYTHONPATH
          value: "/app"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai-key
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: anthropic-key
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8004
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8004
          initialDelaySeconds: 30
          periodSeconds: 10

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: agent-network-ingress
  namespace: agent-network-prod
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/use-regex: "true"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-body-size: "16m"
    nginx.ingress.kubernetes.io/enable-cors: "true"
    nginx.ingress.kubernetes.io/cors-allow-origin: "https://agent-network.com"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - agent-network.com
    secretName: agent-network-tls
  rules:
  - host: agent-network.com
    http:
      paths:
      - path: /api/
        pathType: Prefix
        backend:
          service:
            name: orchestrator-service
            port:
              number: 8004
      - path: /ws/
        pathType: Prefix
        backend:
          service:
            name: orchestrator-service
            port:
              number: 8004
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

### **Pattern 4: Production Configuration Management**

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: frontend-config
  namespace: agent-network-prod
data:
  nginx.conf: |
    # Production nginx configuration with enhanced security
    worker_processes auto;
    error_log /var/log/nginx/error.log warn;
    pid /tmp/nginx.pid;
    
    events {
        worker_connections 2048;
        use epoll;
        multi_accept on;
    }
    
    http {
        include /etc/nginx/mime.types;
        default_type application/octet-stream;
        
        # Security and performance settings
        server_tokens off;
        sendfile on;
        tcp_nopush on;
        tcp_nodelay on;
        keepalive_timeout 65;
        
        # Rate limiting
        limit_req_zone $binary_remote_addr zone=global:10m rate=10r/s;
        limit_req_zone $binary_remote_addr zone=api:10m rate=5r/s;
        limit_conn_zone $binary_remote_addr zone=addr:10m;
        
        # Logging
        log_format json_combined escape=json
          '{'
            '"time_local":"$time_local",'
            '"remote_addr":"$remote_addr",'
            '"remote_user":"$remote_user",'
            '"request":"$request",'
            '"status": "$status",'
            '"body_bytes_sent":"$body_bytes_sent",'
            '"request_time":"$request_time",'
            '"http_referrer":"$http_referer",'
            '"http_user_agent":"$http_user_agent"'
          '}';
        
        access_log /var/log/nginx/access.log json_combined;
        
        server {
            listen 8080 default_server;
            server_name _;
            root /usr/share/nginx/html;
            index index.html;
            
            # Security headers
            add_header X-Frame-Options "DENY" always;
            add_header X-Content-Type-Options "nosniff" always;
            add_header X-XSS-Protection "1; mode=block" always;
            add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
            add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https: wss:; font-src 'self'" always;
            
            # Rate limiting
            limit_req zone=global burst=20 nodelay;
            limit_conn addr 10;
            
            # Health check
            location /health {
                access_log off;
                return 200 "healthy\n";
                add_header Content-Type text/plain;
            }
            
            # Static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
                add_header Vary "Accept-Encoding";
                gzip_static on;
            }
            
            # SPA routing
            location / {
                try_files $uri $uri/ /index.html;
                add_header Cache-Control "no-cache, no-store, must-revalidate";
                add_header Pragma "no-cache";
                add_header Expires "0";
            }
        }
    }

---
# k8s/secrets.yaml (template - use real secrets)
apiVersion: v1
kind: Secret
metadata:
  name: api-keys
  namespace: agent-network-prod
type: Opaque
data:
  openai-key: <base64-encoded-key>
  anthropic-key: <base64-encoded-key>

---
apiVersion: v1
kind: Secret
metadata:
  name: database-secret
  namespace: agent-network-prod
type: Opaque
data:
  url: <base64-encoded-database-url>
```

## 📊 **Monitoring and Observability**

### **Pattern 5: Application Monitoring**

```typescript
// src/utils/monitoring.ts
interface MetricEvent {
  name: string
  value: number
  labels?: Record<string, string>
  timestamp?: Date
}

interface ErrorEvent {
  message: string
  stack?: string
  context?: Record<string, any>
  severity: 'low' | 'medium' | 'high' | 'critical'
  userId?: string
  sessionId: string
}

class ProductionMonitoring {
  private metricsEndpoint: string
  private errorEndpoint: string
  private batchSize = 10
  private flushInterval = 5000
  
  private metricsBatch: MetricEvent[] = []
  private errorsBatch: ErrorEvent[] = []
  private flushTimer?: NodeJS.Timeout

  constructor() {
    this.metricsEndpoint = process.env.REACT_APP_METRICS_ENDPOINT || ''
    this.errorEndpoint = process.env.REACT_APP_ERRORS_ENDPOINT || ''
    
    this.setupFlushTimer()
    this.setupUnloadHandler()
    this.setupPerformanceObserver()
  }

  // Track custom metrics
  recordMetric(name: string, value: number, labels?: Record<string, string>): void {
    const event: MetricEvent = {
      name,
      value,
      labels,
      timestamp: new Date()
    }

    this.metricsBatch.push(event)
    
    if (this.metricsBatch.length >= this.batchSize) {
      this.flushMetrics()
    }
  }

  // Track streaming performance
  recordStreamingMetrics(stats: {
    totalUpdates: number
    droppedUpdates: number
    averageLatency: number
    queueSize: number
  }): void {
    this.recordMetric('streaming_updates_total', stats.totalUpdates)
    this.recordMetric('streaming_updates_dropped', stats.droppedUpdates)
    this.recordMetric('streaming_latency_avg', stats.averageLatency)
    this.recordMetric('streaming_queue_size', stats.queueSize)
    
    // Alert on performance issues
    if (stats.droppedUpdates > 10) {
      this.recordError({
        message: 'High number of dropped streaming updates',
        context: { stats },
        severity: 'medium',
        sessionId: this.getSessionId()
      })
    }
  }

  // Track user interactions
  recordUserAction(action: string, context?: Record<string, any>): void {
    this.recordMetric('user_action', 1, { action })
    
    // Track specific high-value actions
    if (['message_sent', 'conversation_started', 'agent_switched'].includes(action)) {
      this.recordMetric(`action_${action}`, 1, context)
    }
  }

  // Track API responses
  recordApiResponse(
    endpoint: string, 
    method: string, 
    status: number, 
    duration: number
  ): void {
    this.recordMetric('api_request_duration', duration, {
      endpoint,
      method,
      status: status.toString()
    })
    
    this.recordMetric('api_request_total', 1, {
      endpoint,
      method,
      status_class: Math.floor(status / 100).toString() + 'xx'
    })
  }

  // Track errors with context
  recordError(error: Omit<ErrorEvent, 'sessionId'> & { sessionId?: string }): void {
    const errorEvent: ErrorEvent = {
      ...error,
      sessionId: error.sessionId || this.getSessionId()
    }

    this.errorsBatch.push(errorEvent)
    
    // Immediate flush for critical errors
    if (error.severity === 'critical') {
      this.flushErrors()
    }
    
    if (this.errorsBatch.length >= this.batchSize) {
      this.flushErrors()
    }
  }

  // Track page performance
  recordPageLoad(timing: PerformanceTiming): void {
    const loadTime = timing.loadEventEnd - timing.navigationStart
    const domContentLoaded = timing.domContentLoadedEventEnd - timing.navigationStart
    const firstByte = timing.responseStart - timing.navigationStart
    
    this.recordMetric('page_load_time', loadTime)
    this.recordMetric('dom_content_loaded_time', domContentLoaded)
    this.recordMetric('time_to_first_byte', firstByte)
  }

  // Track memory usage
  recordMemoryUsage(): void {
    if ((performance as any).memory) {
      const memory = (performance as any).memory
      this.recordMetric('memory_used', memory.usedJSHeapSize)
      this.recordMetric('memory_total', memory.totalJSHeapSize)
      this.recordMetric('memory_limit', memory.jsHeapSizeLimit)
      
      // Alert on high memory usage
      const usage = memory.usedJSHeapSize / memory.jsHeapSizeLimit
      if (usage > 0.8) {
        this.recordError({
          message: 'High memory usage detected',
          context: { usage, memory },
          severity: 'medium',
          sessionId: this.getSessionId()
        })
      }
    }
  }

  private setupFlushTimer(): void {
    this.flushTimer = setInterval(() => {
      this.flushMetrics()
      this.flushErrors()
    }, this.flushInterval)
  }

  private setupUnloadHandler(): void {
    window.addEventListener('beforeunload', () => {
      this.flushMetrics()
      this.flushErrors()
    })
  }

  private setupPerformanceObserver(): void {
    if (window.PerformanceObserver) {
      // Observe long tasks that block the main thread
      try {
        const longTaskObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.duration > 50) { // Tasks longer than 50ms
              this.recordMetric('long_task_duration', entry.duration)
              
              if (entry.duration > 200) {
                this.recordError({
                  message: 'Long task detected',
                  context: { duration: entry.duration, name: entry.name },
                  severity: 'medium',
                  sessionId: this.getSessionId()
                })
              }
            }
          }
        })
        longTaskObserver.observe({ entryTypes: ['longtask'] })
      } catch (e) {
        // Long task API not supported
      }

      // Observe paint metrics
      try {
        const paintObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            this.recordMetric(`paint_${entry.name.replace(/-/g, '_')}`, entry.startTime)
          }
        })
        paintObserver.observe({ entryTypes: ['paint'] })
      } catch (e) {
        // Paint API not supported
      }
    }
  }

  private async flushMetrics(): Promise<void> {
    if (this.metricsBatch.length === 0 || !this.metricsEndpoint) return

    const batch = [...this.metricsBatch]
    this.metricsBatch = []

    try {
      await fetch(this.metricsEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ metrics: batch }),
        keepalive: true
      })
    } catch (error) {
      // Silently fail metrics collection - don't impact user experience
      console.warn('Failed to send metrics:', error)
    }
  }

  private async flushErrors(): Promise<void> {
    if (this.errorsBatch.length === 0 || !this.errorEndpoint) return

    const batch = [...this.errorsBatch]
    this.errorsBatch = []

    try {
      await fetch(this.errorEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ errors: batch }),
        keepalive: true
      })
    } catch (error) {
      console.warn('Failed to send errors:', error)
    }
  }

  private getSessionId(): string {
    let sessionId = sessionStorage.getItem('monitoring-session-id')
    if (!sessionId) {
      sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      sessionStorage.setItem('monitoring-session-id', sessionId)
    }
    return sessionId
  }

  destroy(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer)
    }
    
    // Final flush
    this.flushMetrics()
    this.flushErrors()
  }
}

export const monitoring = new ProductionMonitoring()

// React hook for easy monitoring integration
export const useMonitoring = () => {
  useEffect(() => {
    // Track page load
    if (document.readyState === 'complete') {
      monitoring.recordPageLoad(performance.timing)
    } else {
      window.addEventListener('load', () => {
        monitoring.recordPageLoad(performance.timing)
      })
    }

    // Track memory usage periodically
    const memoryInterval = setInterval(() => {
      monitoring.recordMemoryUsage()
    }, 30000)

    return () => {
      clearInterval(memoryInterval)
    }
  }, [])

  return {
    recordMetric: monitoring.recordMetric.bind(monitoring),
    recordUserAction: monitoring.recordUserAction.bind(monitoring),
    recordError: monitoring.recordError.bind(monitoring),
    recordApiResponse: monitoring.recordApiResponse.bind(monitoring),
    recordStreamingMetrics: monitoring.recordStreamingMetrics.bind(monitoring),
  }
}
```

### **Pattern 6: Prometheus Metrics Configuration**

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  # Frontend application metrics
  - job_name: 'frontend'
    static_configs:
      - targets: ['frontend:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s

  # Orchestrator service metrics
  - job_name: 'orchestrator'
    static_configs:
      - targets: ['orchestrator:8004']
    metrics_path: '/metrics'
    scrape_interval: 15s

  # Agent services
  - job_name: 'a2a-math-agent'
    static_configs:
      - targets: ['a2a-math-agent:8002']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'acp-hello-world'
    static_configs:
      - targets: ['acp-hello-world:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s

  # Infrastructure
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

---
# monitoring/alert_rules.yml
groups:
  - name: frontend_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(frontend_errors_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate in frontend"
          description: "Frontend error rate is {{ $value }} errors per second"

      - alert: HighMemoryUsage
        expr: frontend_memory_usage_ratio > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage in frontend"
          description: "Frontend memory usage is {{ $value }}%"

      - alert: StreamingPerformanceDegradation
        expr: frontend_streaming_latency_avg > 200
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "Streaming performance degradation"
          description: "Average streaming latency is {{ $value }}ms"

  - name: orchestrator_alerts
    rules:
      - alert: OrchestratorDown
        expr: up{job="orchestrator"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Orchestrator service is down"
          description: "Orchestrator has been down for more than 1 minute"

      - alert: HighAgentResponseTime
        expr: orchestrator_agent_response_time_seconds > 5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High agent response time"
          description: "Agent response time is {{ $value }}s"
```

## 🔐 **Security Hardening**

### **Pattern 7: Production Security Configuration**

```typescript
// src/utils/security.ts
export class SecurityManager {
  private cspNonce?: string

  constructor() {
    this.setupCSP()
    this.setupSecurityHeaders()
    this.validateEnvironment()
  }

  private setupCSP(): void {
    // Generate nonce for inline scripts
    this.cspNonce = this.generateNonce()
    
    const csp = {
      'default-src': ["'self'"],
      'script-src': [
        "'self'", 
        `'nonce-${this.cspNonce}'`,
        'https://cdn.jsdelivr.net' // For any CDN resources
      ],
      'style-src': [
        "'self'", 
        "'unsafe-inline'" // Required for CSS-in-JS
      ],
      'img-src': [
        "'self'", 
        'data:', 
        'https:'
      ],
      'connect-src': [
        "'self'",
        process.env.REACT_APP_API_URL || '',
        process.env.REACT_APP_WS_URL || '',
        // Add monitoring endpoints
        process.env.REACT_APP_METRICS_ENDPOINT || '',
        process.env.REACT_APP_ERRORS_ENDPOINT || ''
      ].filter(Boolean),
      'font-src': ["'self'"],
      'object-src': ["'none'"],
      'media-src': ["'self'"],
      'frame-src': ["'none'"],
      'base-uri': ["'self'"],
      'form-action': ["'self'"],
      'frame-ancestors': ["'none'"],
      'upgrade-insecure-requests': []
    }

    const cspString = Object.entries(csp)
      .map(([key, values]) => `${key} ${values.join(' ')}`)
      .join('; ')

    const meta = document.createElement('meta')
    meta.httpEquiv = 'Content-Security-Policy'
    meta.content = cspString
    document.head.appendChild(meta)
  }

  private setupSecurityHeaders(): void {
    // These would typically be set by the server, but we can validate they exist
    const expectedHeaders = [
      'X-Frame-Options',
      'X-Content-Type-Options', 
      'X-XSS-Protection',
      'Strict-Transport-Security'
    ]

    // In development, warn if security headers are missing
    if (process.env.NODE_ENV === 'development') {
      expectedHeaders.forEach(header => {
        // Check if header would be blocked (indicates it's set)
        fetch('/', { method: 'HEAD' }).then(response => {
          if (!response.headers.get(header.toLowerCase())) {
            console.warn(`Security header missing: ${header}`)
          }
        }).catch(() => {
          // Expected in development
        })
      })
    }
  }

  private validateEnvironment(): void {
    const requiredEnvVars = [
      'REACT_APP_API_URL',
      'REACT_APP_WS_URL'
    ]

    const missingVars = requiredEnvVars.filter(
      varName => !process.env[varName]
    )

    if (missingVars.length > 0) {
      throw new Error(`Missing required environment variables: ${missingVars.join(', ')}`)
    }

    // Validate URLs are HTTPS in production
    if (process.env.NODE_ENV === 'production') {
      const apiUrl = process.env.REACT_APP_API_URL
      const wsUrl = process.env.REACT_APP_WS_URL
      
      if (apiUrl && !apiUrl.startsWith('https://')) {
        throw new Error('API_URL must use HTTPS in production')
      }
      
      if (wsUrl && !wsUrl.startsWith('wss://')) {
        throw new Error('WS_URL must use WSS in production')
      }
    }
  }

  // Sanitize user input
  sanitizeInput(input: string): string {
    return input
      .replace(/[<>]/g, '') // Remove potential HTML tags
      .replace(/javascript:/gi, '') // Remove javascript: URLs
      .replace(/on\w+=/gi, '') // Remove event handlers
      .trim()
  }

  // Validate message content
  validateMessage(message: string): boolean {
    if (!message || message.length === 0) return false
    if (message.length > 10000) return false // Max message length
    
    // Check for suspicious patterns
    const suspiciousPatterns = [
      /<script/i,
      /javascript:/i,
      /on\w+=/i,
      /data:text\/html/i
    ]

    return !suspiciousPatterns.some(pattern => pattern.test(message))
  }

  // Generate secure nonce
  private generateNonce(): string {
    const array = new Uint8Array(16)
    crypto.getRandomValues(array)
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
  }

  getCspNonce(): string | undefined {
    return this.cspNonce
  }
}

export const security = new SecurityManager()
```

## 🎯 **Deployment Automation**

### **Pattern 8: CI/CD Pipeline**

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          
      - name: Install dependencies
        run: npm ci
        
      - name: Run tests
        run: |
          npm run test:unit
          npm run test:integration
          npm run test:e2e
          
      - name: Run security audit
        run: npm audit --audit-level high
        
      - name: Run linting
        run: npm run lint
        
      - name: Type check
        run: npm run type-check

  build:
    needs: test
    runs-on: ubuntu-latest
    outputs:
      image-digest: ${{ steps.build.outputs.digest }}
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Docker Buildx
        uses: docker/setup-buildx-action@v2
        
      - name: Login to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
          
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/frontend
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=sha
            
      - name: Build and push
        id: build
        uses: docker/build-push-action@v4
        with:
          context: .
          file: ./Dockerfile.frontend
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  security-scan:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Scan image for vulnerabilities
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/frontend:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'
          
      - name: Upload scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

  deploy-staging:
    needs: [build, security-scan]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: staging
    steps:
      - name: Deploy to Staging
        run: |
          # Deploy to staging Kubernetes cluster
          echo "Deploying to staging..."
          # kubectl apply commands would go here

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup kubectl
        uses: azure/setup-kubectl@v3
        with:
          version: 'v1.24.0'
          
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2
          
      - name: Update kubeconfig
        run: |
          aws eks update-kubeconfig --name production-cluster --region us-west-2
          
      - name: Deploy to Production
        run: |
          # Update image in deployment
          kubectl set image deployment/frontend frontend=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/frontend:${{ github.sha }} -n agent-network-prod
          
          # Wait for rollout
          kubectl rollout status deployment/frontend -n agent-network-prod --timeout=300s
          
      - name: Run smoke tests
        run: |
          # Run post-deployment tests
          curl -f https://agent-network.com/health || exit 1
          curl -f https://agent-network.com/api/health || exit 1

  notify:
    needs: [deploy-production]
    runs-on: ubuntu-latest
    if: always()
    steps:
      - name: Notify deployment status
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: "Production deployment ${{ job.status }}"
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

## 🎯 **Key Deployment Strategies**

1. **Container-first approach** - Everything runs in containers for consistency
2. **Multi-stage security** - Security scanning at build and runtime
3. **Horizontal scaling** - Auto-scaling based on CPU and memory
4. **Health checks everywhere** - Monitor every service continuously  
5. **Observability built-in** - Metrics and logging from day one
6. **Zero-downtime deployments** - Rolling updates with readiness probes
7. **Infrastructure as Code** - Reproducible environments via YAML

---

**Previous**: [05-testing-strategies.md](./05-testing-strategies.md)

**Back to Architecture Overview**: [README.md](./README.md)