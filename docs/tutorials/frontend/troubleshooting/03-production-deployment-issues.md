# Troubleshooting: Production Deployment Issues

## 🎯 **What You'll Learn**

This production troubleshooting guide covers:
- Common deployment failures and their root causes
- Environment-specific configuration issues
- SSL/TLS and security-related problems
- Performance issues in production environments
- CDN and asset delivery problems
- Docker containerization troubleshooting

## 🚨 **Issue 1: Build Failures in Production**

### **Symptoms**
```bash
# Build fails with errors like:
npm run build
> build

✗ [ERROR] Could not resolve "react-syntax-highlighter/dist/esm/languages/javascript"
✗ [ERROR] Module not found: Can't resolve './config/environment'
✗ [ERROR] TypeScript error: Property 'gtag' does not exist on type 'Window'
```

### **Root Causes & Solutions**

#### **Cause 1: Missing Environment Variables**
```bash
# Check required environment variables
echo "Required variables:"
echo "REACT_APP_API_URL: $REACT_APP_API_URL"
echo "REACT_APP_ENVIRONMENT: $REACT_APP_ENVIRONMENT" 
echo "REACT_APP_VERSION: $REACT_APP_VERSION"
```

**Solution:**
```bash
# .env.production
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_ENVIRONMENT=production
REACT_APP_VERSION=1.0.0
REACT_APP_BUILD_DATE=2024-01-15T10:30:00Z
REACT_APP_SENTRY_DSN=https://your-sentry-dsn
REACT_APP_GA_TRACKING_ID=G-XXXXXXXXXX
```

#### **Cause 2: TypeScript Errors in Production**
```typescript
// src/types/window.d.ts - Add missing global types
declare global {
  interface Window {
    gtag?: (...args: any[]) => void
    Sentry?: any
    dataLayer?: any[]
  }
}

export {}
```

#### **Cause 3: Import Resolution Issues**
```typescript
// Fix dynamic imports in vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      external: (id) => {
        // Don't externalize specific problematic modules
        if (id.includes('react-syntax-highlighter')) {
          return false
        }
        return false
      }
    }
  },
  
  // Ensure proper resolution
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    }
  }
})
```

## 🔒 **Issue 2: SSL/HTTPS Configuration Problems**

### **Symptoms**
```
Mixed Content: The page at 'https://yourdomain.com' was loaded over HTTPS, 
but requested an insecure resource 'http://api.yourdomain.com/health'. 
This request has been blocked.
```

### **Solutions**

#### **Solution 1: Enforce HTTPS in Production**
```typescript
// src/config/environment.ts
export const getApiUrl = (): string => {
  const baseUrl = process.env.REACT_APP_API_URL
  
  if (!baseUrl) {
    throw new Error('REACT_APP_API_URL is required')
  }
  
  // Force HTTPS in production
  if (ENV.environment === 'production' && !baseUrl.startsWith('https://')) {
    console.warn('⚠️ Forcing HTTPS for production API URL')
    return baseUrl.replace('http://', 'https://')
  }
  
  return baseUrl
}
```

#### **Solution 2: Update Nginx Configuration**
```nginx
# nginx.conf - Force HTTPS redirect
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options SAMEORIGIN always;
    add_header X-Content-Type-Options nosniff always;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

## 🌐 **Issue 3: CORS Errors in Production**

### **Symptoms**
```
Access to fetch at 'https://api.yourdomain.com/process' from origin 'https://yourdomain.com' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present
```

### **Debugging Steps**

#### **Step 1: Verify CORS Configuration**
```bash
# Test CORS headers
curl -H "Origin: https://yourdomain.com" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     https://api.yourdomain.com/process \
     -v
```

#### **Step 2: Backend CORS Configuration**
```python
# Backend - Update CORS origins for production
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://www.yourdomain.com",
        # Remove localhost origins in production
    ],
    allow_credentials=True,  # If using authentication
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

#### **Step 3: Production Proxy Configuration**
```nginx
# nginx.conf - Proxy API requests if needed
location /api/ {
    proxy_pass https://backend-service:8004/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # CORS headers (if backend doesn't handle)
    add_header 'Access-Control-Allow-Origin' 'https://yourdomain.com' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range' always;
    
    if ($request_method = 'OPTIONS') {
        add_header 'Access-Control-Allow-Origin' 'https://yourdomain.com';
        add_header 'Access-Control-Max-Age' 1728000;
        add_header 'Content-Type' 'text/plain; charset=utf-8';
        add_header 'Content-Length' 0;
        return 204;
    }
}
```

## 🚀 **Issue 4: Static Asset Loading Problems**

### **Symptoms**
- White screen on production
- 404 errors for JS/CSS files
- Images not loading
- Fonts missing or defaulting

### **Solutions**

#### **Solution 1: Configure Base URL**
```typescript
// vite.config.ts
export default defineConfig({
  base: process.env.NODE_ENV === 'production' ? '/your-path/' : '/',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    
    // Generate manifest for asset tracking
    manifest: true,
    
    rollupOptions: {
      output: {
        // Consistent asset naming
        assetFileNames: (assetInfo) => {
          let extType = assetInfo.name?.split('.').at(-1)
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(extType ?? '')) {
            extType = 'images'
          }
          return `${extType}/[name]-[hash][extname]`
        },
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
      }
    }
  }
})
```

#### **Solution 2: CDN Configuration**
```html
<!-- public/index.html -->
<head>
  <link rel="preconnect" href="https://cdn.yourdomain.com">
  <link rel="dns-prefetch" href="https://api.yourdomain.com">
  
  <!-- Preload critical assets -->
  <link rel="preload" href="/fonts/inter-var.woff2" as="font" type="font/woff2" crossorigin>
</head>
```

```nginx
# nginx.conf - Asset caching
location ~* \.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, no-transform, immutable";
    add_header Vary Accept-Encoding;
    
    # Gzip compression
    gzip_static on;
    gzip_vary on;
}
```

## 📊 **Issue 5: Performance Problems in Production**

### **Symptoms**
- Slow page load times
- High memory usage
- Poor Core Web Vitals scores
- Unresponsive UI during interactions

### **Debugging Tools**

#### **Performance Profiling**
```typescript
// src/utils/productionProfiler.ts
class ProductionProfiler {
  static measurePageLoad() {
    window.addEventListener('load', () => {
      setTimeout(() => {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
        
        const metrics = {
          dns: navigation.domainLookupEnd - navigation.domainLookupStart,
          connect: navigation.connectEnd - navigation.connectStart,
          ttfb: navigation.responseStart - navigation.requestStart,
          download: navigation.responseEnd - navigation.responseStart,
          domParse: navigation.domContentLoadedEventStart - navigation.responseEnd,
          totalLoad: navigation.loadEventEnd - navigation.navigationStart
        }
        
        console.log('🚀 Production Performance Metrics:', metrics)
        
        // Alert on poor performance
        if (metrics.totalLoad > 3000) {
          console.warn('⚠️ Slow page load detected:', metrics.totalLoad + 'ms')
        }
      }, 0)
    })
  }
}

// Initialize in production
if (process.env.NODE_ENV === 'production') {
  ProductionProfiler.measurePageLoad()
}
```

#### **Memory Leak Detection**
```typescript
// src/utils/memoryMonitor.ts
class MemoryMonitor {
  private intervalId: number | null = null
  
  start() {
    if (this.intervalId || !('memory' in performance)) return
    
    this.intervalId = window.setInterval(() => {
      const memory = (performance as any).memory
      const usedMB = Math.round(memory.usedJSHeapSize / 1024 / 1024)
      
      if (usedMB > 150) { // Alert at 150MB
        console.error('🚨 High memory usage detected:', usedMB + 'MB')
        
        // Send alert to monitoring service
        if (window.Sentry) {
          window.Sentry.captureMessage(
            `High memory usage: ${usedMB}MB`,
            'warning'
          )
        }
      }
    }, 60000) // Check every minute
  }
  
  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId)
      this.intervalId = null
    }
  }
}

export const memoryMonitor = new MemoryMonitor()
```

### **Solution: Production Optimization**
```typescript
// src/main.tsx - Production optimizations
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

// Production-only imports
if (process.env.NODE_ENV === 'production') {
  // Lazy load monitoring tools
  import('./utils/productionProfiler')
  import('./utils/memoryMonitor').then(({ memoryMonitor }) => {
    memoryMonitor.start()
  })
  
  // Initialize error tracking
  import('./utils/errorTracking').then(({ errorTracker }) => {
    errorTracker.init()
  })
}

const root = ReactDOM.createRoot(document.getElementById('root')!)

// Use concurrent features in production
if (process.env.NODE_ENV === 'production') {
  root.render(<App />)
} else {
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  )
}
```

## 🐳 **Issue 6: Docker Containerization Problems**

### **Symptoms**
```bash
# Build fails in Docker
ERROR [build 6/7] RUN npm run build
npm ERR! Missing script: "build"

# Container exits immediately
docker run frontend-app
Container exited with code 127
```

### **Solutions**

#### **Multi-Stage Dockerfile Debugging**
```dockerfile
# Dockerfile with debugging
FROM node:18-alpine AS builder

# Add debugging
RUN node --version && npm --version

WORKDIR /app

# Copy package files first (better caching)
COPY package*.json ./
RUN npm ci --only=production

# Debug: Check installed packages
RUN npm list --depth=0

# Copy source and build
COPY . .

# Debug: List files before build
RUN ls -la

# Set build arguments
ARG REACT_APP_API_URL
ARG REACT_APP_ENVIRONMENT=production
ENV REACT_APP_API_URL=$REACT_APP_API_URL
ENV REACT_APP_ENVIRONMENT=$REACT_APP_ENVIRONMENT

# Debug: Check environment
RUN env | grep REACT_APP

# Build with error handling
RUN npm run build && ls -la dist/

# Production stage
FROM nginx:alpine AS production

# Debug: Check nginx
RUN nginx -v

# Copy built app
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

# Debug: Verify files copied
RUN ls -la /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### **Docker Compose Production Setup**
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  frontend:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        REACT_APP_API_URL: ${REACT_APP_API_URL:-https://api.yourdomain.com}
        REACT_APP_ENVIRONMENT: production
        REACT_APP_VERSION: ${VERSION:-latest}
    
    ports:
      - "80:80"
      - "443:443"
    
    environment:
      - NODE_ENV=production
    
    volumes:
      # SSL certificates
      - ./ssl:/etc/nginx/ssl:ro
      # Logs
      - ./logs/nginx:/var/log/nginx
    
    restart: unless-stopped
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`yourdomain.com`)"
      - "traefik.http.routers.frontend.tls.certresolver=letsencrypt"

  # Add monitoring
  watchtower:
    image: containrrr/watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    command: --interval 300 # Check every 5 minutes
```

## 🔧 **Issue 7: Environment Configuration Problems**

### **Symptoms**
- Features work in development but fail in production
- API endpoints returning 404 in production
- Authentication/authorization failures
- Feature flags not working correctly

### **Solution: Environment Validation**
```typescript
// src/config/environmentValidator.ts
interface EnvironmentRequirements {
  required: string[]
  optional: string[]
  validation: Record<string, (value: string) => boolean>
}

const PRODUCTION_REQUIREMENTS: EnvironmentRequirements = {
  required: [
    'REACT_APP_API_URL',
    'REACT_APP_ENVIRONMENT',
    'REACT_APP_VERSION'
  ],
  optional: [
    'REACT_APP_SENTRY_DSN',
    'REACT_APP_GA_TRACKING_ID',
    'REACT_APP_LOG_LEVEL'
  ],
  validation: {
    REACT_APP_API_URL: (value) => {
      try {
        const url = new URL(value)
        return url.protocol === 'https:' || url.hostname === 'localhost'
      } catch {
        return false
      }
    },
    REACT_APP_ENVIRONMENT: (value) => ['development', 'staging', 'production'].includes(value),
    REACT_APP_VERSION: (value) => /^\d+\.\d+\.\d+/.test(value)
  }
}

export function validateEnvironment(): { isValid: boolean; errors: string[] } {
  const errors: string[] = []
  const env = process.env
  
  // Check required variables
  for (const variable of PRODUCTION_REQUIREMENTS.required) {
    if (!env[variable]) {
      errors.push(`Missing required environment variable: ${variable}`)
    }
  }
  
  // Validate variable formats
  for (const [variable, validator] of Object.entries(PRODUCTION_REQUIREMENTS.validation)) {
    const value = env[variable]
    if (value && !validator(value)) {
      errors.push(`Invalid format for ${variable}: ${value}`)
    }
  }
  
  // Production-specific checks
  if (env.REACT_APP_ENVIRONMENT === 'production') {
    if (!env.REACT_APP_SENTRY_DSN) {
      errors.push('REACT_APP_SENTRY_DSN recommended for production error tracking')
    }
    
    if (env.REACT_APP_API_URL?.startsWith('http://') && !env.REACT_APP_API_URL.includes('localhost')) {
      errors.push('Production API should use HTTPS')
    }
  }
  
  return {
    isValid: errors.length === 0,
    errors
  }
}
```

## 🎯 **Deployment Checklist**

### **Pre-Deployment**
- [ ] All environment variables configured
- [ ] SSL certificates valid and installed
- [ ] CORS configured for production domains
- [ ] Build process tested locally
- [ ] Docker images built and tested
- [ ] Health checks implemented
- [ ] Monitoring and alerting configured

### **Post-Deployment**
- [ ] Health endpoint returns 200
- [ ] All pages load correctly
- [ ] API connections working
- [ ] SSL certificate verified
- [ ] Performance metrics within targets
- [ ] Error tracking receiving events
- [ ] Analytics data flowing

### **Monitoring Setup**
- [ ] Uptime monitoring (Pingdom, StatusCake)
- [ ] Error tracking (Sentry)
- [ ] Performance monitoring (Web Vitals)
- [ ] Log aggregation (ELK stack, Datadog)
- [ ] Resource monitoring (CPU, memory, disk)

## 🎯 **Key Takeaways**

1. **Test production builds locally** - Catch issues before deployment
2. **Validate environment configuration** - Missing variables cause silent failures
3. **Implement proper health checks** - Monitor application status continuously
4. **Use staging environments** - Test production-like conditions
5. **Monitor everything** - Logs, errors, performance, and uptime
6. **Have rollback plans** - Be prepared to revert problematic deployments
7. **Document deployment procedures** - Ensure team consistency

---

**Next**: [Complete Troubleshooting Guide](../README.md#troubleshooting)

**Previous**: [02-api-integration-debugging.md](./02-api-integration-debugging.md)