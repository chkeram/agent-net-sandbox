# Architecture 6: Deployment and Monitoring - Production-Ready Deployment Strategies

## 🎯 **Learning Objectives**

By the end of this tutorial, you will understand:
- Complete deployment pipeline for React applications with streaming capabilities
- Production environment configuration and optimization strategies
- Monitoring, logging, and observability patterns for chat applications
- Error tracking and performance monitoring in production
- Scaling strategies for high-traffic streaming applications
- Security considerations and best practices for production deployment

## 🚀 **The Deployment Challenge**

Production deployment of streaming chat applications requires:
- **High Availability**: Zero-downtime deployments and failover strategies
- **Performance**: Optimized bundles and CDN delivery
- **Scalability**: Auto-scaling for varying traffic patterns
- **Monitoring**: Real-time insights into application health
- **Security**: Protection against common web vulnerabilities
- **Error Recovery**: Graceful handling of service failures

**Our goal**: Build **production-ready deployment** with comprehensive monitoring and observability.

## 🏗️ **Deployment Architecture Overview**

### **Production Stack**

```
┌─────────────────────────────────────────────────────────┐
│                    CDN (CloudFlare/AWS)                 │
├─────────────────────────────────────────────────────────┤
│              Load Balancer (AWS ALB/GCP LB)             │
├─────────────────────────────────────────────────────────┤
│  React App (S3/Vercel) ←→ API Gateway ←→ Orchestrator   │
├─────────────────────────────────────────────────────────┤
│         Monitoring Stack (DataDog/New Relic)            │
├─────────────────────────────────────────────────────────┤
│     Error Tracking (Sentry) + Analytics (LogRocket)     │
└─────────────────────────────────────────────────────────┘
```

### **Step 1: Build Configuration**

```typescript
// vite.config.production.ts
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'
import { visualizer } from 'rollup-plugin-visualizer'
import { compression } from 'vite-plugin-compression'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  
  return {
    plugins: [
      react({
        // Production optimizations
        babel: {
          plugins: [
            // Remove PropTypes in production
            mode === 'production' && 'babel-plugin-transform-react-remove-prop-types',
            // Remove dev-only code
            mode === 'production' && ['babel-plugin-transform-remove-console', {
              exclude: ['error', 'warn']
            }]
          ].filter(Boolean)
        }
      }),
      
      // Bundle analyzer
      visualizer({
        filename: 'dist/stats.html',
        open: true,
        gzipSize: true,
        brotliSize: true
      }),
      
      // Compression
      compression({
        algorithm: 'gzip',
        ext: '.gz'
      }),
      compression({
        algorithm: 'brotliCompress',
        ext: '.br'
      })
    ],
    
    build: {
      target: 'es2015',
      outDir: 'dist',
      assetsDir: 'assets',
      
      // Optimize chunk splitting
      rollupOptions: {
        output: {
          manualChunks: {
            // Vendor chunk for stable libraries
            vendor: [
              'react',
              'react-dom',
              'react-router-dom'
            ],
            
            // UI components chunk
            ui: [
              'lucide-react',
              '@radix-ui/react-dialog',
              '@radix-ui/react-dropdown-menu'
            ],
            
            // Utilities chunk
            utils: [
              'date-fns',
              'clsx',
              'tailwind-merge'
            ]
          }
        }
      },
      
      // Bundle size optimizations
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: ['log', 'debug', 'info'],
          drop_debugger: true,
          pure_funcs: ['console.log', 'console.debug', 'console.info']
        },
        mangle: {
          safari10: true
        }
      },
      
      // Source maps for production debugging
      sourcemap: mode === 'production' ? 'hidden' : true,
      
      // Asset optimization
      assetsInlineLimit: 4096,
      
      // Performance budgets
      chunkSizeWarningLimit: 1000
    },
    
    // Optimize dependencies
    optimizeDeps: {
      include: [
        'react',
        'react-dom',
        'react-router-dom'
      ],
      exclude: [
        // Exclude dev-only dependencies
        '@testing-library/react',
        '@testing-library/jest-dom'
      ]
    },
    
    // Environment variables
    define: {
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
      __BUILD_DATE__: JSON.stringify(new Date().toISOString()),
      __DEPLOYMENT_ENV__: JSON.stringify(mode)
    },
    
    // Development server for local testing
    server: {
      port: 3000,
      host: true,
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8004',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '')
        }
      }
    },
    
    preview: {
      port: 4173,
      host: true
    }
  }
})
```

### **Step 2: Environment Configuration**

```typescript
// src/config/environment.ts
export interface EnvironmentConfig {
  apiUrl: string
  websocketUrl: string
  cdnUrl: string
  enableAnalytics: boolean
  enableErrorTracking: boolean
  logLevel: 'debug' | 'info' | 'warn' | 'error'
  featureFlags: Record<string, boolean>
  performance: {
    enablePerfMonitoring: boolean
    sampleRate: number
    enableWebVitals: boolean
  }
  security: {
    enableCSP: boolean
    enableSRI: boolean
    trustedDomains: string[]
  }
}

class EnvironmentManager {
  private config: EnvironmentConfig

  constructor() {
    this.config = this.loadConfig()
    this.validateConfig()
  }

  private loadConfig(): EnvironmentConfig {
    const env = import.meta.env

    return {
      apiUrl: env.VITE_API_URL || 'http://localhost:8004',
      websocketUrl: env.VITE_WS_URL || 'ws://localhost:8004',
      cdnUrl: env.VITE_CDN_URL || '',
      
      enableAnalytics: env.VITE_ENABLE_ANALYTICS === 'true',
      enableErrorTracking: env.VITE_ENABLE_ERROR_TRACKING === 'true',
      logLevel: (env.VITE_LOG_LEVEL as any) || 'info',
      
      featureFlags: {
        enableConversationThreading: env.VITE_FF_CONVERSATION_THREADING === 'true',
        enableAdvancedSearch: env.VITE_FF_ADVANCED_SEARCH === 'true',
        enableMessageExport: env.VITE_FF_MESSAGE_EXPORT === 'true',
        enablePerformanceMonitoring: env.VITE_FF_PERFORMANCE_MONITORING === 'true',
        enableBetaFeatures: env.VITE_FF_BETA_FEATURES === 'true',
      },
      
      performance: {
        enablePerfMonitoring: env.VITE_ENABLE_PERF_MONITORING === 'true',
        sampleRate: parseFloat(env.VITE_PERF_SAMPLE_RATE || '0.1'),
        enableWebVitals: env.VITE_ENABLE_WEB_VITALS === 'true',
      },
      
      security: {
        enableCSP: env.VITE_ENABLE_CSP === 'true',
        enableSRI: env.VITE_ENABLE_SRI === 'true',
        trustedDomains: (env.VITE_TRUSTED_DOMAINS || '').split(',').filter(Boolean),
      }
    }
  }

  private validateConfig(): void {
    const { apiUrl, websocketUrl } = this.config

    // Validate required URLs
    if (!apiUrl || !this.isValidUrl(apiUrl)) {
      throw new Error('Invalid API URL configuration')
    }

    if (!websocketUrl || !this.isValidUrl(websocketUrl.replace('ws', 'http'))) {
      throw new Error('Invalid WebSocket URL configuration')
    }

    // Validate performance config
    const { sampleRate } = this.config.performance
    if (sampleRate < 0 || sampleRate > 1) {
      console.warn('Performance sample rate should be between 0 and 1')
      this.config.performance.sampleRate = Math.max(0, Math.min(1, sampleRate))
    }
  }

  private isValidUrl(url: string): boolean {
    try {
      new URL(url)
      return true
    } catch {
      return false
    }
  }

  getConfig(): EnvironmentConfig {
    return { ...this.config }
  }

  isFeatureEnabled(feature: keyof EnvironmentConfig['featureFlags']): boolean {
    return this.config.featureFlags[feature] || false
  }

  isDevelopment(): boolean {
    return import.meta.env.DEV
  }

  isProduction(): boolean {
    return import.meta.env.PROD
  }

  getVersion(): string {
    return __APP_VERSION__ || 'unknown'
  }

  getBuildDate(): string {
    return __BUILD_DATE__ || 'unknown'
  }

  getEnvironment(): string {
    return __DEPLOYMENT_ENV__ || 'development'
  }
}

export const environmentManager = new EnvironmentManager()
export default environmentManager
```

### **Step 3: Production Monitoring Setup**

```typescript
// src/services/productionMonitoring.ts
import { environmentManager } from '../config/environment'

interface MonitoringEvent {
  name: string
  properties?: Record<string, any>
  timestamp?: Date
  userId?: string
  sessionId?: string
}

interface PerformanceMetric {
  name: string
  value: number
  unit: string
  tags?: Record<string, string>
  timestamp?: Date
}

interface ErrorReport {
  error: Error
  context?: Record<string, any>
  userId?: string
  sessionId?: string
  timestamp?: Date
  stack?: string
  fingerprint?: string
}

class ProductionMonitoringService {
  private config = environmentManager.getConfig()
  private userId?: string
  private sessionId: string
  private initialized = false

  constructor() {
    this.sessionId = this.generateSessionId()
    this.initializeIfNeeded()
  }

  private initializeIfNeeded(): void {
    if (this.initialized || !environmentManager.isProduction()) return

    this.initializeErrorTracking()
    this.initializePerformanceMonitoring()
    this.initializeAnalytics()
    this.initializeWebVitals()
    
    this.initialized = true
  }

  private generateSessionId(): string {
    return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }

  private initializeErrorTracking(): void {
    if (!this.config.enableErrorTracking) return

    // Initialize Sentry
    if (typeof window !== 'undefined' && (window as any).Sentry) {
      const Sentry = (window as any).Sentry

      Sentry.init({
        dsn: process.env.VITE_SENTRY_DSN,
        environment: environmentManager.getEnvironment(),
        release: environmentManager.getVersion(),
        
        // Performance monitoring
        tracesSampleRate: this.config.performance.sampleRate,
        
        // Session tracking
        beforeSend: (event: any) => {
          // Add session context
          event.extra = {
            ...event.extra,
            sessionId: this.sessionId,
            userId: this.userId,
            buildDate: environmentManager.getBuildDate(),
          }
          return event
        },

        // Filter errors
        beforeSendTransaction: (event: any) => {
          // Don't track dev-only transactions
          if (event.transaction?.includes('__dev__')) {
            return null
          }
          return event
        }
      })

      // Set user context
      Sentry.setContext('app', {
        version: environmentManager.getVersion(),
        environment: environmentManager.getEnvironment(),
        buildDate: environmentManager.getBuildDate(),
      })
    }
  }

  private initializePerformanceMonitoring(): void {
    if (!this.config.performance.enablePerfMonitoring) return

    // Initialize performance observer
    if ('PerformanceObserver' in window) {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.trackPerformanceMetric({
            name: `performance.${entry.entryType}.${entry.name}`,
            value: entry.duration || entry.startTime,
            unit: 'ms',
            tags: {
              entryType: entry.entryType,
              name: entry.name
            }
          })
        }
      })

      observer.observe({ entryTypes: ['measure', 'navigation', 'resource'] })
    }

    // Track custom metrics
    this.setupCustomPerformanceTracking()
  }

  private initializeAnalytics(): void {
    if (!this.config.enableAnalytics) return

    // Initialize Google Analytics
    if (process.env.VITE_GA_TRACKING_ID && typeof window !== 'undefined') {
      const script = document.createElement('script')
      script.async = true
      script.src = `https://www.googletagmanager.com/gtag/js?id=${process.env.VITE_GA_TRACKING_ID}`
      document.head.appendChild(script)

      // Initialize gtag
      ;(window as any).dataLayer = (window as any).dataLayer || []
      const gtag = (...args: any[]) => (window as any).dataLayer.push(arguments)
      ;(window as any).gtag = gtag

      gtag('js', new Date())
      gtag('config', process.env.VITE_GA_TRACKING_ID, {
        session_id: this.sessionId,
        custom_map: {
          custom_dimension_1: 'app_version'
        }
      })

      gtag('event', 'app_version', {
        custom_parameter: environmentManager.getVersion()
      })
    }
  }

  private initializeWebVitals(): void {
    if (!this.config.performance.enableWebVitals) return

    // Import web-vitals dynamically
    import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
      getCLS(this.reportWebVital.bind(this))
      getFID(this.reportWebVital.bind(this))
      getFCP(this.reportWebVital.bind(this))
      getLCP(this.reportWebVital.bind(this))
      getTTFB(this.reportWebVital.bind(this))
    }).catch(error => {
      console.warn('Failed to load web-vitals:', error)
    })
  }

  private reportWebVital(metric: any): void {
    this.trackPerformanceMetric({
      name: `web_vitals.${metric.name}`,
      value: metric.value,
      unit: 'ms',
      tags: {
        id: metric.id,
        rating: metric.rating
      }
    })

    // Send to analytics
    if (this.config.enableAnalytics && typeof (window as any).gtag === 'function') {
      ;(window as any).gtag('event', metric.name, {
        event_category: 'Web Vitals',
        event_label: metric.id,
        value: Math.round(metric.name === 'CLS' ? metric.value * 1000 : metric.value),
        non_interaction: true
      })
    }
  }

  private setupCustomPerformanceTracking(): void {
    // Track React render performance
    if (typeof window !== 'undefined') {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.name.includes('react')) {
            this.trackPerformanceMetric({
              name: 'react.render.duration',
              value: entry.duration,
              unit: 'ms',
              tags: {
                component: entry.name
              }
            })
          }
        }
      })

      try {
        observer.observe({ entryTypes: ['measure'] })
      } catch (error) {
        console.warn('Performance observer not supported:', error)
      }
    }
  }

  /**
   * Set user context for all monitoring services
   */
  setUser(userId: string, userProperties?: Record<string, any>): void {
    this.userId = userId

    // Update Sentry context
    if (typeof window !== 'undefined' && (window as any).Sentry) {
      ;(window as any).Sentry.setUser({
        id: userId,
        ...userProperties
      })
    }

    // Update analytics context
    if (this.config.enableAnalytics && typeof (window as any).gtag === 'function') {
      ;(window as any).gtag('config', process.env.VITE_GA_TRACKING_ID, {
        user_id: userId,
        custom_map: {
          custom_dimension_2: 'user_type'
        }
      })
    }
  }

  /**
   * Track custom events
   */
  trackEvent(event: MonitoringEvent): void {
    const eventData = {
      ...event,
      timestamp: event.timestamp || new Date(),
      userId: event.userId || this.userId,
      sessionId: event.sessionId || this.sessionId,
    }

    // Send to analytics
    if (this.config.enableAnalytics && typeof (window as any).gtag === 'function') {
      ;(window as any).gtag('event', event.name, {
        event_category: 'User Interaction',
        ...event.properties
      })
    }

    // Log for debugging
    if (environmentManager.isDevelopment()) {
      console.log('📊 Event:', eventData)
    }

    // Send to custom analytics endpoint if configured
    this.sendToAnalyticsEndpoint(eventData)
  }

  /**
   * Track performance metrics
   */
  trackPerformanceMetric(metric: PerformanceMetric): void {
    const metricData = {
      ...metric,
      timestamp: metric.timestamp || new Date(),
      tags: {
        ...metric.tags,
        sessionId: this.sessionId,
        userId: this.userId || 'anonymous',
        environment: environmentManager.getEnvironment(),
        version: environmentManager.getVersion(),
      }
    }

    // Log for debugging
    if (environmentManager.isDevelopment()) {
      console.log('📈 Metric:', metricData)
    }

    // Send to monitoring service
    this.sendToMetricsEndpoint(metricData)
  }

  /**
   * Report errors to monitoring services
   */
  reportError(report: ErrorReport): void {
    const errorData = {
      ...report,
      timestamp: report.timestamp || new Date(),
      userId: report.userId || this.userId,
      sessionId: report.sessionId || this.sessionId,
      stack: report.stack || report.error.stack,
      fingerprint: report.fingerprint || this.generateErrorFingerprint(report.error),
    }

    // Send to Sentry
    if (this.config.enableErrorTracking && typeof window !== 'undefined' && (window as any).Sentry) {
      ;(window as any).Sentry.captureException(report.error, {
        extra: errorData.context,
        user: {
          id: errorData.userId,
          sessionId: errorData.sessionId,
        },
        fingerprint: [errorData.fingerprint!]
      })
    }

    // Log for debugging
    if (environmentManager.isDevelopment()) {
      console.error('🚨 Error Report:', errorData)
    }

    // Send to custom error endpoint
    this.sendToErrorEndpoint(errorData)
  }

  private generateErrorFingerprint(error: Error): string {
    const message = error.message || 'Unknown error'
    const stack = error.stack?.split('\n')[1] || 'Unknown stack'
    return btoa(`${error.name}-${message}-${stack}`).slice(0, 32)
  }

  private async sendToAnalyticsEndpoint(event: MonitoringEvent): Promise<void> {
    if (!environmentManager.isProduction()) return

    try {
      await fetch('/api/analytics/events', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(event),
      })
    } catch (error) {
      console.warn('Failed to send analytics event:', error)
    }
  }

  private async sendToMetricsEndpoint(metric: PerformanceMetric): Promise<void> {
    if (!environmentManager.isProduction()) return

    try {
      await fetch('/api/monitoring/metrics', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(metric),
      })
    } catch (error) {
      console.warn('Failed to send performance metric:', error)
    }
  }

  private async sendToErrorEndpoint(errorData: ErrorReport): Promise<void> {
    if (!environmentManager.isProduction()) return

    try {
      await fetch('/api/monitoring/errors', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: errorData.error.message,
          stack: errorData.stack,
          context: errorData.context,
          userId: errorData.userId,
          sessionId: errorData.sessionId,
          timestamp: errorData.timestamp,
          fingerprint: errorData.fingerprint,
        }),
      })
    } catch (error) {
      console.warn('Failed to send error report:', error)
    }
  }

  /**
   * Get session information
   */
  getSessionInfo() {
    return {
      sessionId: this.sessionId,
      userId: this.userId,
      version: environmentManager.getVersion(),
      environment: environmentManager.getEnvironment(),
      buildDate: environmentManager.getBuildDate(),
    }
  }
}

export const productionMonitoring = new ProductionMonitoringService()
export default productionMonitoring
```

### **Step 4: Docker Configuration**

```dockerfile
# Dockerfile
# Multi-stage build for optimal production image
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json yarn.lock ./

# Install dependencies
RUN yarn install --frozen-lockfile --production=false

# Copy source code
COPY . .

# Build application
ARG NODE_ENV=production
ARG VITE_API_URL
ARG VITE_ENABLE_ANALYTICS=true
ARG VITE_ENABLE_ERROR_TRACKING=true

ENV NODE_ENV=$NODE_ENV
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_ENABLE_ANALYTICS=$VITE_ENABLE_ANALYTICS
ENV VITE_ENABLE_ERROR_TRACKING=$VITE_ENABLE_ERROR_TRACKING

RUN yarn build

# Production stage
FROM nginx:alpine

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy security headers configuration
COPY security-headers.conf /etc/nginx/conf.d/security-headers.conf

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/ || exit 1

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

```nginx
# nginx.conf
server {
    listen 80;
    server_name localhost;
    
    # Security headers
    include /etc/nginx/conf.d/security-headers.conf;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;
    
    # Brotli compression (if available)
    brotli on;
    brotli_comp_level 4;
    brotli_types
        text/plain
        text/css
        application/json
        application/javascript
        text/xml
        application/xml
        application/xml+rss
        text/javascript;
    
    # Main application
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            add_header Vary "Accept-Encoding";
        }
        
        # Don't cache HTML files
        location ~* \.html$ {
            expires -1;
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
        }
    }
    
    # API proxy (if needed)
    location /api/ {
        proxy_pass http://api-backend:8004/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
    
    # Metrics endpoint for monitoring
    location /metrics {
        access_log off;
        return 200 "# HELP nginx_up Nginx is running\n# TYPE nginx_up gauge\nnginx_up 1\n";
        add_header Content-Type text/plain;
    }
}
```

```nginx
# security-headers.conf
# Security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

# Remove server signature
server_tokens off;
```

### **Step 5: CI/CD Pipeline**

```yaml
# .github/workflows/deploy-production.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '18'
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}/frontend

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'yarn'
          
      - name: Install dependencies
        run: yarn install --frozen-lockfile
        
      - name: Run linting
        run: yarn lint
        
      - name: Run type checking
        run: yarn type-check
        
      - name: Run unit tests
        run: yarn test:coverage
        
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage/lcov.info
          
      - name: Run E2E tests
        run: |
          yarn build
          yarn preview &
          yarn test:e2e
          
  security:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        
      - name: Run security audit
        run: yarn audit --level moderate
        
      - name: Run dependency vulnerability scan
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
          
  build:
    runs-on: ubuntu-latest
    needs: [test, security]
    if: github.ref == 'refs/heads/main'
    
    outputs:
      image-digest: ${{ steps.build.outputs.digest }}
      
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'yarn'
          
      - name: Install dependencies
        run: yarn install --frozen-lockfile
        
      - name: Build application
        env:
          VITE_API_URL: ${{ secrets.PRODUCTION_API_URL }}
          VITE_ENABLE_ANALYTICS: true
          VITE_ENABLE_ERROR_TRACKING: true
          VITE_GA_TRACKING_ID: ${{ secrets.GA_TRACKING_ID }}
          VITE_SENTRY_DSN: ${{ secrets.SENTRY_DSN }}
        run: yarn build
        
      - name: Analyze bundle size
        run: |
          yarn analyze-bundle
          echo "Bundle analysis complete"
          
      - name: Setup Docker Buildx
        uses: docker/setup-buildx-action@v2
        
      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
          
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}
            
      - name: Build and push Docker image
        id: build
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          build-args: |
            NODE_ENV=production
            VITE_API_URL=${{ secrets.PRODUCTION_API_URL }}
            VITE_ENABLE_ANALYTICS=true
            VITE_ENABLE_ERROR_TRACKING=true
          cache-from: type=gha
          cache-to: type=gha,mode=max
          
  deploy:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment: production
    
    steps:
      - name: Deploy to production
        env:
          IMAGE_DIGEST: ${{ needs.build.outputs.image-digest }}
        run: |
          echo "Deploying image with digest: $IMAGE_DIGEST"
          # Deploy to your infrastructure (AWS ECS, Kubernetes, etc.)
          
      - name: Run smoke tests
        run: |
          # Wait for deployment to be ready
          sleep 30
          
          # Run basic smoke tests
          curl -f https://your-app.com/health || exit 1
          curl -f https://your-app.com/ || exit 1
          
      - name: Notify deployment success
        uses: 8398a7/action-slack@v3
        with:
          status: success
          text: "🚀 Frontend deployed successfully to production!"
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
          
      - name: Update monitoring
        run: |
          # Notify monitoring services of deployment
          curl -X POST "${{ secrets.DEPLOYMENT_WEBHOOK_URL }}" \
            -H "Content-Type: application/json" \
            -d '{
              "deployment": {
                "environment": "production",
                "version": "${{ github.sha }}",
                "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
              }
            }'
```

### **Step 6: Health Checks and Status Monitoring**

```typescript
// src/services/healthCheck.ts
interface HealthCheckResult {
  service: string
  status: 'healthy' | 'degraded' | 'unhealthy'
  responseTime: number
  details?: string
  timestamp: Date
}

interface SystemHealth {
  overall: 'healthy' | 'degraded' | 'unhealthy'
  services: HealthCheckResult[]
  version: string
  uptime: number
  timestamp: Date
}

class HealthCheckService {
  private checks = new Map<string, () => Promise<HealthCheckResult>>()
  private startTime = Date.now()

  constructor() {
    this.registerDefaultChecks()
  }

  private registerDefaultChecks(): void {
    // API health check
    this.registerCheck('api', async () => {
      const start = performance.now()
      
      try {
        const response = await fetch('/api/health', {
          method: 'GET',
          timeout: 5000
        } as RequestInit)
        
        const responseTime = performance.now() - start
        
        if (response.ok) {
          return {
            service: 'api',
            status: 'healthy',
            responseTime,
            timestamp: new Date()
          }
        } else {
          return {
            service: 'api',
            status: 'unhealthy',
            responseTime,
            details: `HTTP ${response.status}: ${response.statusText}`,
            timestamp: new Date()
          }
        }
      } catch (error) {
        const responseTime = performance.now() - start
        return {
          service: 'api',
          status: 'unhealthy',
          responseTime,
          details: error instanceof Error ? error.message : 'Unknown error',
          timestamp: new Date()
        }
      }
    })

    // Local storage health check
    this.registerCheck('storage', async () => {
      const start = performance.now()
      
      try {
        const testKey = 'health-check-test'
        const testValue = Date.now().toString()
        
        localStorage.setItem(testKey, testValue)
        const retrieved = localStorage.getItem(testKey)
        localStorage.removeItem(testKey)
        
        const responseTime = performance.now() - start
        
        if (retrieved === testValue) {
          return {
            service: 'storage',
            status: 'healthy',
            responseTime,
            timestamp: new Date()
          }
        } else {
          return {
            service: 'storage',
            status: 'unhealthy',
            responseTime,
            details: 'Local storage test failed',
            timestamp: new Date()
          }
        }
      } catch (error) {
        const responseTime = performance.now() - start
        return {
          service: 'storage',
          status: 'unhealthy',
          responseTime,
          details: error instanceof Error ? error.message : 'Storage error',
          timestamp: new Date()
        }
      }
    })

    // WebSocket connectivity check
    this.registerCheck('websocket', async () => {
      const start = performance.now()
      
      return new Promise<HealthCheckResult>((resolve) => {
        try {
          const wsUrl = environmentManager.getConfig().websocketUrl
          const ws = new WebSocket(wsUrl)
          
          const timeout = setTimeout(() => {
            ws.close()
            resolve({
              service: 'websocket',
              status: 'unhealthy',
              responseTime: performance.now() - start,
              details: 'Connection timeout',
              timestamp: new Date()
            })
          }, 5000)
          
          ws.onopen = () => {
            clearTimeout(timeout)
            ws.close()
            resolve({
              service: 'websocket',
              status: 'healthy',
              responseTime: performance.now() - start,
              timestamp: new Date()
            })
          }
          
          ws.onerror = (error) => {
            clearTimeout(timeout)
            resolve({
              service: 'websocket',
              status: 'unhealthy',
              responseTime: performance.now() - start,
              details: 'WebSocket connection failed',
              timestamp: new Date()
            })
          }
        } catch (error) {
          resolve({
            service: 'websocket',
            status: 'unhealthy',
            responseTime: performance.now() - start,
            details: error instanceof Error ? error.message : 'WebSocket error',
            timestamp: new Date()
          })
        }
      })
    })
  }

  registerCheck(name: string, checkFn: () => Promise<HealthCheckResult>): void {
    this.checks.set(name, checkFn)
  }

  async runHealthChecks(): Promise<SystemHealth> {
    const checkPromises = Array.from(this.checks.entries()).map(
      async ([name, checkFn]) => {
        try {
          return await checkFn()
        } catch (error) {
          return {
            service: name,
            status: 'unhealthy' as const,
            responseTime: 0,
            details: error instanceof Error ? error.message : 'Check failed',
            timestamp: new Date()
          }
        }
      }
    )

    const results = await Promise.all(checkPromises)
    
    // Determine overall health
    const unhealthyCount = results.filter(r => r.status === 'unhealthy').length
    const degradedCount = results.filter(r => r.status === 'degraded').length
    
    let overall: SystemHealth['overall']
    if (unhealthyCount > 0) {
      overall = 'unhealthy'
    } else if (degradedCount > 0) {
      overall = 'degraded'
    } else {
      overall = 'healthy'
    }

    return {
      overall,
      services: results,
      version: environmentManager.getVersion(),
      uptime: Date.now() - this.startTime,
      timestamp: new Date()
    }
  }

  async getHealthStatus(): Promise<SystemHealth> {
    return this.runHealthChecks()
  }

  startPeriodicHealthChecks(intervalMs = 60000): void {
    setInterval(async () => {
      try {
        const health = await this.runHealthChecks()
        
        // Report to monitoring
        productionMonitoring.trackEvent({
          name: 'health_check',
          properties: {
            overall_status: health.overall,
            unhealthy_services: health.services
              .filter(s => s.status === 'unhealthy')
              .map(s => s.service)
          }
        })

        // Log if unhealthy
        if (health.overall !== 'healthy') {
          console.warn('System health degraded:', health)
        }
      } catch (error) {
        console.error('Health check failed:', error)
      }
    }, intervalMs)
  }
}

export const healthCheck = new HealthCheckService()
export default healthCheck
```

## 🎯 **Production Optimization Checklist**

### **Performance**
- [ ] Bundle size < 500KB (gzipped)
- [ ] First Contentful Paint < 2s
- [ ] Largest Contentful Paint < 2.5s
- [ ] Time to Interactive < 3s
- [ ] Cumulative Layout Shift < 0.1
- [ ] Code splitting implemented
- [ ] Tree shaking enabled
- [ ] Image optimization
- [ ] CDN configuration

### **Security**
- [ ] HTTPS enforced
- [ ] Content Security Policy
- [ ] Subresource Integrity
- [ ] X-Frame-Options set
- [ ] X-Content-Type-Options set
- [ ] Secure headers configured
- [ ] Dependencies audited
- [ ] Environment variables secured

### **Monitoring**
- [ ] Error tracking active
- [ ] Performance monitoring
- [ ] User analytics
- [ ] Health checks configured
- [ ] Uptime monitoring
- [ ] Log aggregation
- [ ] Alerting configured

### **Reliability**
- [ ] Load balancing
- [ ] Auto-scaling
- [ ] Graceful error handling
- [ ] Circuit breaker patterns
- [ ] Retry mechanisms
- [ ] Fallback strategies
- [ ] Database backups

## 🎯 **Key Takeaways**

1. **Build optimization is critical** - Proper bundling and compression reduce load times
2. **Monitor everything in production** - Comprehensive monitoring catches issues early
3. **Security headers are essential** - Protect against common web vulnerabilities
4. **Automate deployments** - CI/CD pipelines reduce human error
5. **Health checks enable proactive response** - Know about issues before users do
6. **Performance budgets prevent regression** - Set limits and enforce them
7. **Error tracking improves user experience** - Fix issues users never report

---

**Previous**: [05-testing-strategies.md](./05-testing-strategies.md)

**Back to Architecture Overview**: [README.md](./README.md)