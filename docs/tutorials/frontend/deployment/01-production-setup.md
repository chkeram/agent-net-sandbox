# Production Deployment: Frontend Setup & Configuration

## 🎯 **What You'll Learn**

This comprehensive production guide covers:
- Building and optimizing React applications for production
- Environment configuration and secrets management
- CDN setup and asset optimization
- SSL/TLS configuration and security headers
- Performance monitoring and error tracking
- Docker containerization for consistent deployments

## 🏗️ **Build Process & Optimization**

### **Step 1: Production Build Configuration**

```typescript
// vite.config.ts - Production optimizations
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  const isDev = mode === 'development'
  
  return {
    plugins: [react()],
    
    // Build optimization
    build: {
      target: 'es2015',
      outDir: 'dist',
      assetsDir: 'assets',
      
      // Enable source maps in production for debugging
      sourcemap: true,
      
      // Chunk splitting for better caching
      rollupOptions: {
        output: {
          manualChunks: {
            // Vendor chunk for libraries that rarely change
            vendor: ['react', 'react-dom'],
            
            // UI chunk for component libraries  
            ui: ['lucide-react', 'react-syntax-highlighter'],
            
            // Utils chunk for utilities
            utils: ['date-fns', 'uuid'],
          },
        },
      },
      
      // Compression and minification
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: !isDev, // Remove console.logs in production
          drop_debugger: true,
        },
      },
      
      // Asset optimization
      assetsInlineLimit: 4096, // Inline assets smaller than 4kb
    },
    
    // Development proxy
    server: isDev ? {
      proxy: {
        '/api': {
          target: 'http://localhost:8004',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    } : {},
    
    // Path resolution
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
        '@components': resolve(__dirname, 'src/components'),
        '@services': resolve(__dirname, 'src/services'),
        '@types': resolve(__dirname, 'src/types'),
      },
    },
  }
})
```

### **Step 2: Environment Configuration**

```bash
# .env.production
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_ENVIRONMENT=production
REACT_APP_VERSION=$npm_package_version
REACT_APP_BUILD_DATE=$BUILD_DATE

# Security settings
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_SENTRY_DSN=https://your-sentry-dsn
REACT_APP_LOG_LEVEL=error

# Feature flags
REACT_APP_ENABLE_STREAMING=true
REACT_APP_ENABLE_PROTOCOL_DEBUG=false
REACT_APP_ENABLE_PERFORMANCE_MONITORING=true
```

```typescript
// src/config/environment.ts
interface EnvironmentConfig {
  apiUrl: string
  environment: 'development' | 'staging' | 'production'
  version: string
  buildDate: string
  enableAnalytics: boolean
  sentryDsn?: string
  logLevel: 'debug' | 'info' | 'warn' | 'error'
  features: {
    streaming: boolean
    protocolDebug: boolean
    performanceMonitoring: boolean
  }
}

const getEnvironmentConfig = (): EnvironmentConfig => {
  // Validate required environment variables
  const apiUrl = process.env.REACT_APP_API_URL
  if (!apiUrl) {
    throw new Error('REACT_APP_API_URL is required')
  }
  
  return {
    apiUrl,
    environment: (process.env.REACT_APP_ENVIRONMENT as any) || 'development',
    version: process.env.REACT_APP_VERSION || '0.0.0',
    buildDate: process.env.REACT_APP_BUILD_DATE || new Date().toISOString(),
    enableAnalytics: process.env.REACT_APP_ENABLE_ANALYTICS === 'true',
    sentryDsn: process.env.REACT_APP_SENTRY_DSN,
    logLevel: (process.env.REACT_APP_LOG_LEVEL as any) || 'info',
    features: {
      streaming: process.env.REACT_APP_ENABLE_STREAMING !== 'false',
      protocolDebug: process.env.REACT_APP_ENABLE_PROTOCOL_DEBUG === 'true',
      performanceMonitoring: process.env.REACT_APP_ENABLE_PERFORMANCE_MONITORING === 'true',
    },
  }
}

export const ENV = getEnvironmentConfig()

// Runtime validation
console.log('🌍 Environment:', ENV.environment)
console.log('🔗 API URL:', ENV.apiUrl)
console.log('📦 Version:', ENV.version)

// Development-only logs
if (ENV.environment === 'development') {
  console.log('🔧 Full config:', ENV)
}
```

### **Step 3: Build Scripts and CI/CD**

```json
{
  "scripts": {
    "build": "tsc && vite build",
    "build:staging": "cross-env REACT_APP_ENVIRONMENT=staging vite build",
    "build:production": "cross-env REACT_APP_ENVIRONMENT=production vite build",
    "build:analyze": "vite build && npx vite-bundle-analyzer dist/stats.json",
    "preview": "vite preview",
    "deploy:staging": "npm run build:staging && aws s3 sync dist/ s3://staging-bucket",
    "deploy:production": "npm run build:production && aws s3 sync dist/ s3://production-bucket"
  }
}
```

```yaml
# .github/workflows/deploy.yml
name: Deploy Frontend

on:
  push:
    branches: [main, staging]
  pull_request:
    branches: [main]

jobs:
  build-and-deploy:
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
        run: npm run test:ci
      
      - name: Run linting
        run: npm run lint
      
      - name: Type check
        run: npm run type-check
      
      - name: Build for staging
        if: github.ref == 'refs/heads/staging'
        run: npm run build:staging
        env:
          REACT_APP_API_URL: ${{ secrets.STAGING_API_URL }}
          REACT_APP_SENTRY_DSN: ${{ secrets.SENTRY_DSN }}
          BUILD_DATE: ${{ github.event.head_commit.timestamp }}
      
      - name: Build for production  
        if: github.ref == 'refs/heads/main'
        run: npm run build:production
        env:
          REACT_APP_API_URL: ${{ secrets.PRODUCTION_API_URL }}
          REACT_APP_SENTRY_DSN: ${{ secrets.SENTRY_DSN }}
          BUILD_DATE: ${{ github.event.head_commit.timestamp }}
      
      - name: Deploy to S3 Staging
        if: github.ref == 'refs/heads/staging'
        run: aws s3 sync dist/ s3://${{ secrets.STAGING_S3_BUCKET }} --delete
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      
      - name: Deploy to S3 Production
        if: github.ref == 'refs/heads/main'
        run: aws s3 sync dist/ s3://${{ secrets.PRODUCTION_S3_BUCKET }} --delete
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      
      - name: Invalidate CloudFront
        if: github.ref == 'refs/heads/main'
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }} \
            --paths "/*"
```

## 🐳 **Docker Containerization**

### **Multi-Stage Dockerfile**

```dockerfile
# Dockerfile
# Stage 1: Build the application
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy source code
COPY . .

# Build arguments for environment variables
ARG REACT_APP_API_URL
ARG REACT_APP_ENVIRONMENT=production
ARG REACT_APP_VERSION
ARG BUILD_DATE

# Set environment variables
ENV REACT_APP_API_URL=$REACT_APP_API_URL
ENV REACT_APP_ENVIRONMENT=$REACT_APP_ENVIRONMENT
ENV REACT_APP_VERSION=$REACT_APP_VERSION
ENV REACT_APP_BUILD_DATE=$BUILD_DATE

# Build the application
RUN npm run build

# Stage 2: Serve the application with nginx
FROM nginx:alpine AS production

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built application from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Add labels for metadata
LABEL maintainer="your-team@company.com"
LABEL version=$REACT_APP_VERSION
LABEL description="Agent Network Sandbox Frontend"

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

### **Nginx Configuration**

```nginx
# nginx.conf
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    access_log /var/log/nginx/access.log main;
    
    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    server {
        listen 80;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'; frame-ancestors 'self';" always;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            access_log off;
        }
        
        # Handle client-side routing
        location / {
            try_files $uri $uri/ /index.html;
        }
        
        # API proxy (if needed)
        location /api/ {
            proxy_pass http://orchestrator:8004/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
            
            # CORS headers for API requests
            add_header 'Access-Control-Allow-Origin' '*';
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
            add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range';
            
            if ($request_method = 'OPTIONS') {
                add_header 'Access-Control-Allow-Origin' '*';
                add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
                add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range';
                add_header 'Access-Control-Max-Age' 1728000;
                add_header 'Content-Type' 'text/plain; charset=utf-8';
                add_header 'Content-Length' 0;
                return 204;
            }
        }
        
        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
        
        # Error pages
        error_page 404 /404.html;
        error_page 500 502 503 504 /50x.html;
    }
}
```

### **Docker Compose for Production**

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  frontend:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        REACT_APP_API_URL: ${REACT_APP_API_URL}
        REACT_APP_VERSION: ${REACT_APP_VERSION:-latest}
        BUILD_DATE: ${BUILD_DATE}
    
    ports:
      - "80:80"
      - "443:443"
    
    environment:
      - NODE_ENV=production
    
    volumes:
      # SSL certificates (if handling SSL in container)
      - ./ssl:/etc/nginx/ssl:ro
      
      # Logs
      - ./logs/nginx:/var/log/nginx
    
    restart: unless-stopped
    
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`yourdomain.com`)"
      - "traefik.http.routers.frontend.tls.certresolver=letsencrypt"
    
    networks:
      - frontend-network
    
    depends_on:
      - orchestrator
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  orchestrator:
    image: agent-orchestrator:latest
    ports:
      - "8004:8004"
    networks:
      - frontend-network

networks:
  frontend-network:
    driver: bridge
```

## 🔒 **Security Configuration**

### **Content Security Policy**

```html
<!-- public/index.html - Security headers -->
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
  style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
  font-src 'self' https://fonts.gstatic.com;
  img-src 'self' data: blob: https:;
  connect-src 'self' https://api.yourdomain.com wss://api.yourdomain.com;
  frame-ancestors 'none';
  form-action 'self';
  base-uri 'self';
">

<!-- Additional security headers -->
<meta http-equiv="X-Content-Type-Options" content="nosniff">
<meta http-equiv="X-Frame-Options" content="DENY">
<meta http-equiv="X-XSS-Protection" content="1; mode=block">
<meta name="referrer" content="no-referrer-when-downgrade">
```

### **Environment Variable Validation**

```typescript
// src/utils/security.ts
export const validateEnvironment = () => {
  const requiredVars = [
    'REACT_APP_API_URL',
    'REACT_APP_ENVIRONMENT',
  ]
  
  const missingVars = requiredVars.filter(
    varName => !process.env[varName]
  )
  
  if (missingVars.length > 0) {
    throw new Error(`Missing required environment variables: ${missingVars.join(', ')}`)
  }
  
  // Validate API URL format
  const apiUrl = process.env.REACT_APP_API_URL!
  try {
    new URL(apiUrl)
  } catch {
    throw new Error(`Invalid REACT_APP_API_URL format: ${apiUrl}`)
  }
  
  // Production-specific validations
  if (process.env.REACT_APP_ENVIRONMENT === 'production') {
    if (!apiUrl.startsWith('https://')) {
      console.warn('⚠️ API URL should use HTTPS in production')
    }
    
    if (!process.env.REACT_APP_SENTRY_DSN) {
      console.warn('⚠️ SENTRY_DSN not configured for production error tracking')
    }
  }
}

// Run validation on app startup
validateEnvironment()
```

## 📊 **Performance Monitoring Setup**

### **Error Tracking with Sentry**

```typescript
// src/utils/errorTracking.ts
import * as Sentry from '@sentry/react'
import { BrowserTracing } from '@sentry/tracing'
import { ENV } from '../config/environment'

// Initialize Sentry for production error tracking
if (ENV.environment === 'production' && ENV.sentryDsn) {
  Sentry.init({
    dsn: ENV.sentryDsn,
    environment: ENV.environment,
    release: ENV.version,
    
    integrations: [
      new BrowserTracing({
        // Track navigation and user interactions
        routingInstrumentation: Sentry.reactRouterV6Instrumentation(
          React.useEffect,
          useLocation,
          useNavigationType,
          createRoutesFromChildren,
          matchRoutes
        ),
      }),
    ],
    
    // Performance monitoring
    tracesSampleRate: 0.1, // 10% sampling
    
    // Filter out common non-critical errors
    beforeSend(event, hint) {
      // Filter out network errors we can't control
      if (event.exception) {
        const error = hint.originalException
        if (error && error.name === 'NetworkError') {
          return null
        }
      }
      
      return event
    },
    
    // Tag all events with deployment info
    initialScope: {
      tags: {
        version: ENV.version,
        buildDate: ENV.buildDate,
      },
    },
  })
}

export const trackError = (error: Error, context?: any) => {
  console.error('Application Error:', error, context)
  
  if (ENV.environment === 'production') {
    Sentry.captureException(error, {
      extra: context,
    })
  }
}

export const trackPerformance = (name: string, duration: number, tags?: Record<string, string>) => {
  if (ENV.features.performanceMonitoring) {
    Sentry.addBreadcrumb({
      category: 'performance',
      message: `${name}: ${duration}ms`,
      level: 'info',
      data: { duration, ...tags },
    })
  }
}
```

### **Web Vitals Monitoring**

```typescript
// src/utils/webVitals.ts
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals'

const sendToAnalytics = (metric: any) => {
  // Send to your analytics service
  if (window.gtag) {
    window.gtag('event', metric.name, {
      custom_parameter_value: Math.round(metric.value),
      custom_parameter_delta: metric.delta,
      custom_parameter_id: metric.id,
    })
  }
  
  // Also log for debugging
  console.log('Web Vital:', metric)
}

export const reportWebVitals = () => {
  getCLS(sendToAnalytics)
  getFID(sendToAnalytics)
  getFCP(sendToAnalytics)
  getLCP(sendToAnalytics)
  getTTFB(sendToAnalytics)
}
```

### **Usage in Main App**

```typescript
// src/main.tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import { validateEnvironment } from './utils/security'
import { reportWebVitals } from './utils/webVitals'
import './utils/errorTracking' // Initialize Sentry

// Validate environment before starting app
try {
  validateEnvironment()
} catch (error) {
  console.error('Environment validation failed:', error)
  
  // Show user-friendly error in production
  if (process.env.NODE_ENV === 'production') {
    document.body.innerHTML = `
      <div style="padding: 20px; text-align: center; font-family: sans-serif;">
        <h1>Configuration Error</h1>
        <p>The application is not properly configured. Please contact support.</p>
      </div>
    `
    throw error
  }
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

// Report web vitals in production
if (process.env.NODE_ENV === 'production') {
  reportWebVitals()
}
```

## 🎯 **Deployment Checklist**

### **Pre-Deployment**
- [ ] All tests passing (`npm run test`)
- [ ] No TypeScript errors (`npm run type-check`)
- [ ] No linting errors (`npm run lint`)
- [ ] Bundle size analyzed and optimized
- [ ] Environment variables configured correctly
- [ ] Security headers implemented
- [ ] Error tracking configured
- [ ] Performance monitoring enabled

### **Build Verification**
- [ ] Production build completes successfully
- [ ] All assets load correctly in built version
- [ ] API endpoints accessible from production domain
- [ ] CORS configured for production origins
- [ ] SSL certificates valid and configured
- [ ] CDN cache invalidation setup

### **Post-Deployment**
- [ ] Health check endpoint returns 200
- [ ] All major user flows working
- [ ] Error tracking receiving events
- [ ] Performance metrics within acceptable ranges  
- [ ] Logs are being collected
- [ ] Monitoring alerts configured
- [ ] Rollback plan documented

## 🎯 **Key Takeaways**

1. **Optimize for production** - Enable minification, compression, and caching
2. **Secure by default** - Implement CSP, security headers, and input validation
3. **Monitor everything** - Error tracking, performance, and user analytics
4. **Plan for failure** - Health checks, graceful degradation, and rollback procedures
5. **Automate deployment** - CI/CD pipelines reduce human error
6. **Test in production-like environments** - Staging should mirror production
7. **Document thoroughly** - Deployment procedures, rollback plans, and troubleshooting

---

**Next**: [02-performance-optimization.md](./02-performance-optimization.md) - Production Performance Optimization

**Previous**: [Troubleshooting](../troubleshooting/02-api-integration-debugging.md)