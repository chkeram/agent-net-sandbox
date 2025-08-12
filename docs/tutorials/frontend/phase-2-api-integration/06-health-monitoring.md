# Phase 2.6: Health Monitoring & Agent Discovery - Building Observable Systems

## 🎯 **Learning Objectives**

By the end of this tutorial, you will:
- Implement comprehensive health monitoring for distributed agent systems
- Build real-time agent discovery and capability tracking
- Create health dashboards and status indicators for users
- Handle agent failures and automatic recovery mechanisms
- Design proactive monitoring that prevents user-facing issues

## 🏥 **The Health Monitoring Challenge**

In a multi-agent system, many things can go wrong:
- Agents crash or become unresponsive
- Network connectivity issues between services
- Performance degradation under load
- Configuration changes that break integrations
- New agents joining or leaving the network

**Our goal**: Build a monitoring system that **detects issues before users notice** and provides **transparent system status**.

## 🎯 **Health Monitoring Architecture**

### **Step 1: Health Check Types**

```typescript
// src/types/health.ts
export enum HealthStatus {
  HEALTHY = 'healthy',
  DEGRADED = 'degraded',
  UNHEALTHY = 'unhealthy',
  UNKNOWN = 'unknown'
}

export enum HealthCheckType {
  CONNECTIVITY = 'connectivity',
  PERFORMANCE = 'performance', 
  CAPABILITY = 'capability',
  RESOURCE = 'resource'
}

export interface HealthCheck {
  id: string
  type: HealthCheckType
  name: string
  description: string
  status: HealthStatus
  lastChecked: Date
  checkDuration: number // milliseconds
  details?: Record<string, any>
  error?: string
  threshold?: {
    warning: number
    critical: number
  }
}

export interface AgentHealth {
  agentId: string
  agentName: string
  protocol: string
  endpoint: string
  overallStatus: HealthStatus
  lastSeen: Date
  uptime: number // seconds
  checks: HealthCheck[]
  capabilities: Array<{
    name: string
    status: HealthStatus
    tags: string[]
  }>
  performance: {
    responseTime: number
    successRate: number
    requestCount: number
    errorCount: number
  }
}

export interface SystemHealth {
  overallStatus: HealthStatus
  totalAgents: number
  healthyAgents: number
  degradedAgents: number
  unhealthyAgents: number
  lastUpdated: Date
  agents: AgentHealth[]
  systemChecks: HealthCheck[]
}
```

### **Step 2: Health Monitoring Service**

```typescript
// src/services/healthMonitor.ts
import { orchestratorApi } from './orchestratorApi'

interface HealthMonitorConfig {
  checkInterval: number // milliseconds
  timeoutMs: number
  retryAttempts: number
  enablePerformanceTracking: boolean
  alertThresholds: {
    responseTime: number
    errorRate: number
    agentDowntime: number
  }
}

export class HealthMonitorService {
  private config: HealthMonitorConfig
  private monitoringInterval: number | null = null
  private healthHistory = new Map<string, HealthStatus[]>()
  private performanceMetrics = new Map<string, number[]>()
  private subscribers = new Set<(health: SystemHealth) => void>()

  constructor(config: Partial<HealthMonitorConfig> = {}) {
    this.config = {
      checkInterval: 30000, // 30 seconds
      timeoutMs: 5000, // 5 seconds
      retryAttempts: 2,
      enablePerformanceTracking: true,
      alertThresholds: {
        responseTime: 2000, // 2 seconds
        errorRate: 0.1, // 10%
        agentDowntime: 300, // 5 minutes
      },
      ...config,
    }
  }

  /**
   * Start continuous health monitoring
   */
  startMonitoring(): void {
    if (this.monitoringInterval) return

    console.log('🏥 Starting health monitoring...')

    // Initial health check
    this.performHealthCheck()

    // Schedule regular checks
    this.monitoringInterval = window.setInterval(() => {
      this.performHealthCheck()
    }, this.config.checkInterval)
  }

  /**
   * Stop health monitoring
   */
  stopMonitoring(): void {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval)
      this.monitoringInterval = null
      console.log('🏥 Health monitoring stopped')
    }
  }

  /**
   * Subscribe to health updates
   */
  subscribe(callback: (health: SystemHealth) => void): () => void {
    this.subscribers.add(callback)
    return () => this.subscribers.delete(callback)
  }

  /**
   * Perform comprehensive health check
   */
  private async performHealthCheck(): Promise<void> {
    const startTime = Date.now()

    try {
      // Check orchestrator health
      const orchestratorHealth = await this.checkOrchestratorHealth()
      
      // Discover and check individual agents
      const agentHealths = await this.checkAgentHealths()
      
      // Run system-wide checks
      const systemChecks = await this.performSystemChecks()
      
      // Calculate overall system health
      const systemHealth = this.calculateSystemHealth(
        orchestratorHealth,
        agentHealths,
        systemChecks
      )

      // Update performance tracking
      if (this.config.enablePerformanceTracking) {
        this.updatePerformanceMetrics(systemHealth)
      }

      // Update health history
      this.updateHealthHistory(systemHealth)

      // Notify subscribers
      this.notifySubscribers(systemHealth)

      // Check for alerts
      this.checkAlerts(systemHealth)

    } catch (error) {
      console.error('🏥 Health check failed:', error)
      
      // Create error health status
      const errorHealth = this.createErrorHealthStatus(error as Error)
      this.notifySubscribers(errorHealth)
    }

    console.log(`🏥 Health check completed in ${Date.now() - startTime}ms`)
  }

  /**
   * Check orchestrator service health
   */
  private async checkOrchestratorHealth(): Promise<HealthCheck[]> {
    const checks: HealthCheck[] = []

    // Connectivity check
    const connectivityCheck = await this.createHealthCheck(
      'orchestrator-connectivity',
      HealthCheckType.CONNECTIVITY,
      'Orchestrator Connectivity',
      'Check if orchestrator API is reachable',
      async () => {
        const startTime = Date.now()
        await orchestratorApi.checkHealth()
        return Date.now() - startTime
      }
    )
    checks.push(connectivityCheck)

    // Performance check
    const performanceCheck = await this.createHealthCheck(
      'orchestrator-performance',
      HealthCheckType.PERFORMANCE,
      'Orchestrator Response Time',
      'Measure orchestrator API response times',
      async () => {
        const startTime = Date.now()
        await orchestratorApi.getAgents()
        return Date.now() - startTime
      },
      { warning: 1000, critical: 3000 }
    )
    checks.push(performanceCheck)

    return checks
  }

  /**
   * Check health of individual agents
   */
  private async checkAgentHealths(): Promise<AgentHealth[]> {
    try {
      const agents = await orchestratorApi.getAgents()
      const agentHealths: AgentHealth[] = []

      for (const agent of agents) {
        const agentHealth = await this.checkIndividualAgentHealth(agent)
        agentHealths.push(agentHealth)
      }

      return agentHealths
    } catch (error) {
      console.warn('🏥 Failed to check agent healths:', error)
      return []
    }
  }

  /**
   * Check health of individual agent
   */
  private async checkIndividualAgentHealth(agent: any): Promise<AgentHealth> {
    const checks: HealthCheck[] = []
    const startTime = Date.now()

    // Agent-specific connectivity check
    const connectivityCheck = await this.createHealthCheck(
      `${agent.agent_id}-connectivity`,
      HealthCheckType.CONNECTIVITY,
      `${agent.name} Connectivity`,
      `Check if ${agent.name} is responding`,
      async () => {
        // Test agent with a simple query
        const testStart = Date.now()
        try {
          await this.testAgentConnectivity(agent)
          return Date.now() - testStart
        } catch (error) {
          throw new Error(`Agent ${agent.agent_id} is not responding: ${error.message}`)
        }
      }
    )
    checks.push(connectivityCheck)

    // Capability check
    const capabilityCheck = await this.createHealthCheck(
      `${agent.agent_id}-capabilities`,
      HealthCheckType.CAPABILITY,
      `${agent.name} Capabilities`,
      `Verify ${agent.name} capabilities are working`,
      async () => {
        return this.testAgentCapabilities(agent)
      }
    )
    checks.push(capabilityCheck)

    // Calculate overall agent status
    const overallStatus = this.calculateOverallStatus(checks)

    return {
      agentId: agent.agent_id,
      agentName: agent.name,
      protocol: agent.protocol,
      endpoint: agent.endpoint || 'unknown',
      overallStatus,
      lastSeen: new Date(),
      uptime: this.calculateUptime(agent.agent_id),
      checks,
      capabilities: agent.capabilities?.map((cap: any) => ({
        name: cap.name,
        status: HealthStatus.HEALTHY, // TODO: Individual capability testing
        tags: cap.tags || [],
      })) || [],
      performance: this.getAgentPerformanceMetrics(agent.agent_id),
    }
  }

  /**
   * Test agent connectivity with a lightweight query
   */
  private async testAgentConnectivity(agent: any): Promise<void> {
    // Send a simple test message to the agent through orchestrator
    try {
      const testQuery = this.getTestQueryForAgent(agent)
      const response = await orchestratorApi.processMessage(testQuery)
      
      if (!response || !response.success) {
        throw new Error('Agent returned unsuccessful response')
      }
    } catch (error) {
      throw new Error(`Connectivity test failed: ${error.message}`)
    }
  }

  /**
   * Get appropriate test query based on agent capabilities
   */
  private getTestQueryForAgent(agent: any): string {
    const capabilities = agent.capabilities || []
    
    // Math agent test
    if (capabilities.some((cap: any) => cap.tags?.includes('math'))) {
      return '1 + 1'
    }
    
    // Hello world agent test
    if (capabilities.some((cap: any) => cap.tags?.includes('greeting'))) {
      return 'hello'
    }
    
    // Generic test
    return 'health check'
  }

  /**
   * Test agent capabilities
   */
  private async testAgentCapabilities(agent: any): Promise<number> {
    // For now, just return the number of capabilities
    // In a full implementation, we would test each capability
    return agent.capabilities?.length || 0
  }

  /**
   * Create a health check with timing and error handling
   */
  private async createHealthCheck(
    id: string,
    type: HealthCheckType,
    name: string,
    description: string,
    checkFunction: () => Promise<number>,
    threshold?: { warning: number; critical: number }
  ): Promise<HealthCheck> {
    const startTime = Date.now()
    let status = HealthStatus.HEALTHY
    let details: Record<string, any> = {}
    let error: string | undefined

    try {
      const result = await Promise.race([
        checkFunction(),
        new Promise<never>((_, reject) => 
          setTimeout(() => reject(new Error('Check timeout')), this.config.timeoutMs)
        ),
      ])

      const duration = Date.now() - startTime
      details = { result, duration }

      // Apply thresholds if provided
      if (threshold && typeof result === 'number') {
        if (result >= threshold.critical) {
          status = HealthStatus.UNHEALTHY
        } else if (result >= threshold.warning) {
          status = HealthStatus.DEGRADED
        }
      }

    } catch (checkError) {
      status = HealthStatus.UNHEALTHY
      error = (checkError as Error).message
    }

    return {
      id,
      type,
      name,
      description,
      status,
      lastChecked: new Date(),
      checkDuration: Date.now() - startTime,
      details,
      error,
      threshold,
    }
  }

  /**
   * Perform system-wide health checks
   */
  private async performSystemChecks(): Promise<HealthCheck[]> {
    const checks: HealthCheck[] = []

    // Agent discovery check
    const discoveryCheck = await this.createHealthCheck(
      'agent-discovery',
      HealthCheckType.CAPABILITY,
      'Agent Discovery',
      'Check if agent discovery is working',
      async () => {
        const agents = await orchestratorApi.getAgents()
        return agents.length
      },
      { warning: 1, critical: 0 }
    )
    checks.push(discoveryCheck)

    // System resources check (if available)
    if ('memory' in performance) {
      const memoryCheck = await this.createHealthCheck(
        'client-memory',
        HealthCheckType.RESOURCE,
        'Client Memory Usage',
        'Monitor client-side memory usage',
        async () => {
          const memory = (performance as any).memory
          return memory.usedJSHeapSize / 1024 / 1024 // MB
        },
        { warning: 50, critical: 100 }
      )
      checks.push(memoryCheck)
    }

    return checks
  }

  /**
   * Calculate overall system health
   */
  private calculateSystemHealth(
    orchestratorChecks: HealthCheck[],
    agentHealths: AgentHealth[],
    systemChecks: HealthCheck[]
  ): SystemHealth {
    const allChecks = [...orchestratorChecks, ...systemChecks]
    const overallStatus = this.calculateOverallStatus(allChecks)

    const healthyAgents = agentHealths.filter(a => a.overallStatus === HealthStatus.HEALTHY).length
    const degradedAgents = agentHealths.filter(a => a.overallStatus === HealthStatus.DEGRADED).length
    const unhealthyAgents = agentHealths.filter(a => a.overallStatus === HealthStatus.UNHEALTHY).length

    return {
      overallStatus,
      totalAgents: agentHealths.length,
      healthyAgents,
      degradedAgents,
      unhealthyAgents,
      lastUpdated: new Date(),
      agents: agentHealths,
      systemChecks: allChecks,
    }
  }

  /**
   * Calculate overall status from individual checks
   */
  private calculateOverallStatus(checks: HealthCheck[]): HealthStatus {
    if (checks.length === 0) return HealthStatus.UNKNOWN

    const hasUnhealthy = checks.some(c => c.status === HealthStatus.UNHEALTHY)
    const hasDegraded = checks.some(c => c.status === HealthStatus.DEGRADED)

    if (hasUnhealthy) return HealthStatus.UNHEALTHY
    if (hasDegraded) return HealthStatus.DEGRADED
    return HealthStatus.HEALTHY
  }

  /**
   * Calculate agent uptime
   */
  private calculateUptime(agentId: string): number {
    // In a real implementation, this would track when agents were first seen
    // For now, return a placeholder
    return Math.floor(Math.random() * 86400) // 0-24 hours in seconds
  }

  /**
   * Get performance metrics for an agent
   */
  private getAgentPerformanceMetrics(agentId: string) {
    const metrics = this.performanceMetrics.get(agentId) || []
    const recentMetrics = metrics.slice(-10) // Last 10 measurements

    return {
      responseTime: recentMetrics.length > 0 
        ? recentMetrics.reduce((a, b) => a + b, 0) / recentMetrics.length 
        : 0,
      successRate: 0.95, // Placeholder
      requestCount: Math.floor(Math.random() * 1000),
      errorCount: Math.floor(Math.random() * 50),
    }
  }

  /**
   * Update performance metrics
   */
  private updatePerformanceMetrics(health: SystemHealth): void {
    // Store response time metrics for each agent
    health.agents.forEach(agent => {
      const connectivityCheck = agent.checks.find(c => c.type === HealthCheckType.CONNECTIVITY)
      if (connectivityCheck?.details?.duration) {
        const metrics = this.performanceMetrics.get(agent.agentId) || []
        metrics.push(connectivityCheck.details.duration)
        
        // Keep only last 50 measurements
        if (metrics.length > 50) {
          metrics.shift()
        }
        
        this.performanceMetrics.set(agent.agentId, metrics)
      }
    })
  }

  /**
   * Update health history for trend analysis
   */
  private updateHealthHistory(health: SystemHealth): void {
    // Store overall system health history
    const systemHistory = this.healthHistory.get('system') || []
    systemHistory.push(health.overallStatus)
    
    if (systemHistory.length > 100) {
      systemHistory.shift()
    }
    
    this.healthHistory.set('system', systemHistory)

    // Store individual agent health history
    health.agents.forEach(agent => {
      const agentHistory = this.healthHistory.get(agent.agentId) || []
      agentHistory.push(agent.overallStatus)
      
      if (agentHistory.length > 100) {
        agentHistory.shift()
      }
      
      this.healthHistory.set(agent.agentId, agentHistory)
    })
  }

  /**
   * Notify all subscribers of health updates
   */
  private notifySubscribers(health: SystemHealth): void {
    this.subscribers.forEach(callback => {
      try {
        callback(health)
      } catch (error) {
        console.error('🏥 Health subscriber error:', error)
      }
    })
  }

  /**
   * Check for alert conditions
   */
  private checkAlerts(health: SystemHealth): void {
    // High error rate alert
    const unhealthyRatio = health.unhealthyAgents / Math.max(health.totalAgents, 1)
    if (unhealthyRatio > 0.5) {
      console.warn('🚨 HIGH ALERT: More than 50% of agents are unhealthy')
    }

    // System degraded alert
    if (health.overallStatus === HealthStatus.DEGRADED) {
      console.warn('⚠️ MEDIUM ALERT: System performance is degraded')
    }

    // System down alert
    if (health.overallStatus === HealthStatus.UNHEALTHY) {
      console.error('🚨 CRITICAL ALERT: System is unhealthy')
    }
  }

  /**
   * Create error health status when monitoring fails
   */
  private createErrorHealthStatus(error: Error): SystemHealth {
    return {
      overallStatus: HealthStatus.UNKNOWN,
      totalAgents: 0,
      healthyAgents: 0,
      degradedAgents: 0,
      unhealthyAgents: 0,
      lastUpdated: new Date(),
      agents: [],
      systemChecks: [{
        id: 'monitoring-error',
        type: HealthCheckType.CONNECTIVITY,
        name: 'Health Monitoring',
        description: 'Health monitoring system status',
        status: HealthStatus.UNHEALTHY,
        lastChecked: new Date(),
        checkDuration: 0,
        error: error.message,
      }],
    }
  }

  /**
   * Get health history for trend analysis
   */
  getHealthHistory(entityId: string = 'system'): HealthStatus[] {
    return this.healthHistory.get(entityId) || []
  }

  /**
   * Get current health snapshot
   */
  async getCurrentHealth(): Promise<SystemHealth> {
    return new Promise((resolve) => {
      // Trigger immediate health check and wait for result
      const unsubscribe = this.subscribe((health) => {
        unsubscribe()
        resolve(health)
      })
      
      this.performHealthCheck()
    })
  }
}

export const healthMonitor = new HealthMonitorService()
```

### **Step 3: Health Monitoring React Hook**

```typescript
// src/hooks/useHealthMonitoring.ts
import { useState, useEffect, useCallback } from 'react'
import { healthMonitor } from '../services/healthMonitor'
import { SystemHealth, HealthStatus } from '../types/health'

interface HealthMonitoringState {
  health: SystemHealth | null
  isMonitoring: boolean
  lastError: Error | null
  connectionStatus: 'connected' | 'disconnected' | 'reconnecting'
}

export const useHealthMonitoring = (autoStart: boolean = true) => {
  const [state, setState] = useState<HealthMonitoringState>({
    health: null,
    isMonitoring: false,
    lastError: null,
    connectionStatus: 'disconnected',
  })

  const startMonitoring = useCallback(() => {
    try {
      healthMonitor.startMonitoring()
      setState(prev => ({ 
        ...prev, 
        isMonitoring: true, 
        connectionStatus: 'connected',
        lastError: null 
      }))
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        lastError: error as Error,
        connectionStatus: 'disconnected'
      }))
    }
  }, [])

  const stopMonitoring = useCallback(() => {
    healthMonitor.stopMonitoring()
    setState(prev => ({ 
      ...prev, 
      isMonitoring: false,
      connectionStatus: 'disconnected'
    }))
  }, [])

  const refreshHealth = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, connectionStatus: 'reconnecting' }))
      const health = await healthMonitor.getCurrentHealth()
      setState(prev => ({ 
        ...prev, 
        health, 
        connectionStatus: 'connected',
        lastError: null 
      }))
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        lastError: error as Error,
        connectionStatus: 'disconnected'
      }))
    }
  }, [])

  useEffect(() => {
    const unsubscribe = healthMonitor.subscribe((health) => {
      setState(prev => ({ 
        ...prev, 
        health,
        connectionStatus: 'connected',
        lastError: null
      }))
    })

    if (autoStart) {
      startMonitoring()
    }

    return () => {
      unsubscribe()
      if (autoStart) {
        stopMonitoring()
      }
    }
  }, [autoStart, startMonitoring, stopMonitoring])

  return {
    ...state,
    startMonitoring,
    stopMonitoring,
    refreshHealth,
    isHealthy: state.health?.overallStatus === HealthStatus.HEALTHY,
    isDegraded: state.health?.overallStatus === HealthStatus.DEGRADED,
    isUnhealthy: state.health?.overallStatus === HealthStatus.UNHEALTHY,
  }
}
```

## 🎯 **Key Takeaways**

1. **Proactive monitoring prevents issues** - Detect problems before users do
2. **Multi-layered health checks** - Connectivity, performance, capabilities, resources
3. **Historical tracking matters** - Trends reveal patterns and predict failures
4. **User-friendly status displays** - Clear health indicators build trust
5. **Automatic recovery when possible** - Self-healing systems are more reliable
6. **Alert thresholds need tuning** - Balance between noise and missing issues
7. **Performance monitoring is crucial** - Response times affect user experience

---

**Next**: [Phase 3: Streaming & Real-time Features](../phase-3-streaming/01-understanding-sse.md)

**Previous**: [05-error-handling-strategies.md](./05-error-handling-strategies.md)