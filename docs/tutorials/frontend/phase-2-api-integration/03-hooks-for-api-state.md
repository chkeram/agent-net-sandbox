# Phase 2.3: Custom Hooks for API State Management

## 🎯 **Learning Objectives**

By the end of this tutorial, you will:
- Build the complete useOrchestrator custom hook for regular API integration
- Master React hooks patterns for complex API state management
- Implement robust error handling and loading states in custom hooks
- Create reusable hooks that encapsulate business logic
- Understand the difference between streaming and regular API state management

## 🎭 **The Challenge: API State Complexity**

Regular API calls involve multiple states and edge cases:

```
Request Lifecycle:
Idle → Loading → Success (with data) → Idle
   ↘                ↘
    → Error → Retry → Loading...
```

### **State Variables Needed**
- **Loading states**: isLoading, isRefreshing, isRetrying
- **Data states**: agents, health status, last response
- **Error states**: error messages, error types, retry counts
- **Cache management**: last updated, cache invalidation

## 🛠️ **Building useOrchestrator Hook**

### **Step 1: State Interface Design**

```typescript
// src/hooks/useOrchestrator.ts

export interface OrchestratorState {
  // Loading States
  isLoading: boolean;
  isHealthy: boolean | null;  // null = unknown, true/false = known
  isRefreshing: boolean;
  
  // Data States
  agents: AgentSummary[];
  lastResponse: ProcessResponse | null;
  
  // Error States
  error: string | null;
  lastError: Error | null;
  
  // Cache Management
  lastHealthCheck: Date | null;
  lastAgentsRefresh: Date | null;
  
  // Request Statistics
  stats: {
    totalRequests: number;
    successfulRequests: number;
    failedRequests: number;
    averageResponseTime: number;
  };
}

const initialOrchestratorState: OrchestratorState = {
  isLoading: false,
  isHealthy: null,
  isRefreshing: false,
  agents: [],
  lastResponse: null,
  error: null,
  lastError: null,
  lastHealthCheck: null,
  lastAgentsRefresh: null,
  stats: {
    totalRequests: 0,
    successfulRequests: 0,
    failedRequests: 0,
    averageResponseTime: 0,
  },
};
```

### **Step 2: Core Hook Structure**

```typescript
import { useState, useCallback, useEffect, useRef } from 'react';
import { orchestratorApi, ProcessResponse, AgentSummary, HealthResponse } from '../services/orchestratorApi';

export const useOrchestrator = () => {
  const [state, setState] = useState<OrchestratorState>(initialOrchestratorState);
  
  // Use refs for values that don't trigger re-renders
  const abortControllerRef = useRef<AbortController | null>(null);
  const requestStartTimeRef = useRef<number>(0);
  
  // Track component mount status for cleanup
  const isMountedRef = useRef(true);
  
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      // Cleanup any ongoing requests
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);
```

### **Step 3: Error Handling and Statistics**

```typescript
export const useOrchestrator = () => {
  // ... previous state ...
  
  // Helper to safely update state (only if component is mounted)
  const safeSetState = useCallback((updater: (prev: OrchestratorState) => OrchestratorState) => {
    if (isMountedRef.current) {
      setState(updater);
    }
  }, []);
  
  // Update statistics after each request
  const updateStats = useCallback((success: boolean, responseTime: number) => {
    safeSetState(prev => {
      const newStats = {
        totalRequests: prev.stats.totalRequests + 1,
        successfulRequests: prev.stats.successfulRequests + (success ? 1 : 0),
        failedRequests: prev.stats.failedRequests + (success ? 0 : 1),
        averageResponseTime: success 
          ? (prev.stats.averageResponseTime * prev.stats.successfulRequests + responseTime) / (prev.stats.successfulRequests + 1)
          : prev.stats.averageResponseTime,
      };
      
      return {
        ...prev,
        stats: newStats,
      };
    });
  }, [safeSetState]);
  
  // Generic error handler
  const handleError = useCallback((error: unknown, context: string) => {
    const errorObj = error instanceof Error ? error : new Error(String(error));
    const userMessage = getUserFriendlyErrorMessage(errorObj, context);
    
    console.error(`[useOrchestrator] ${context}:`, errorObj);
    
    safeSetState(prev => ({
      ...prev,
      error: userMessage,
      lastError: errorObj,
      isLoading: false,
      isRefreshing: false,
    }));
    
    // Track error in statistics
    const responseTime = Date.now() - requestStartTimeRef.current;
    updateStats(false, responseTime);
  }, [safeSetState, updateStats]);
  
  // Convert technical errors to user-friendly messages
  const getUserFriendlyErrorMessage = (error: Error, context: string): string => {
    if (error.message.includes('NetworkError') || error.message.includes('fetch')) {
      return 'Unable to connect to the orchestrator. Please check your internet connection.';
    }
    
    if (error.message.includes('timeout')) {
      return 'Request timed out. The server may be busy, please try again.';
    }
    
    if (error.message.includes('404')) {
      return 'Orchestrator service not found. Please ensure it\'s running on port 8004.';
    }
    
    if (error.message.includes('500') || error.message.includes('502') || error.message.includes('503')) {
      return 'Server error occurred. Please try again in a moment.';
    }
    
    // Context-specific messages
    switch (context) {
      case 'health-check':
        return 'Health check failed. The orchestrator may be starting up.';
      case 'process-message':
        return 'Failed to process your message. Please try rephrasing or try again.';
      case 'refresh-agents':
        return 'Failed to refresh agents. Using cached agent list.';
      default:
        return error.message || 'An unexpected error occurred.';
    }
  };
```

### **Step 4: Health Monitoring**

```typescript
export const useOrchestrator = () => {
  // ... previous methods ...
  
  const checkHealth = useCallback(async (forceRefresh = false): Promise<boolean> => {
    // Skip if recent health check exists and not forcing refresh
    const HEALTH_CACHE_MS = 30000; // 30 seconds
    if (!forceRefresh && state.lastHealthCheck) {
      const timeSinceCheck = Date.now() - state.lastHealthCheck.getTime();
      if (timeSinceCheck < HEALTH_CACHE_MS && state.isHealthy !== null) {
        return state.isHealthy;
      }
    }
    
    safeSetState(prev => ({ ...prev, isLoading: true, error: null }));
    requestStartTimeRef.current = Date.now();
    
    try {
      // Create abort controller for this request
      const abortController = new AbortController();
      abortControllerRef.current = abortController;
      
      const health: HealthResponse = await orchestratorApi.checkHealth();
      const isHealthy = health.status === 'healthy' && health.agents_discovered > 0;
      
      const responseTime = Date.now() - requestStartTimeRef.current;
      
      safeSetState(prev => ({
        ...prev,
        isLoading: false,
        isHealthy,
        lastHealthCheck: new Date(),
        error: isHealthy ? null : `Only ${health.agents_discovered} agents available`,
      }));
      
      updateStats(true, responseTime);
      abortControllerRef.current = null;
      
      return isHealthy;
      
    } catch (error) {
      // Don't handle aborted requests as errors
      if (error instanceof Error && error.name === 'AbortError') {
        return state.isHealthy ?? false;
      }
      
      handleError(error, 'health-check');
      return false;
    }
  }, [state.lastHealthCheck, state.isHealthy, safeSetState, updateStats, handleError]);
  
  // Auto health check on mount
  useEffect(() => {
    checkHealth();
  }, [checkHealth]);
  
  // Periodic health check
  useEffect(() => {
    const interval = setInterval(() => {
      // Only auto-check if we haven't checked recently
      if (state.lastHealthCheck) {
        const timeSinceCheck = Date.now() - state.lastHealthCheck.getTime();
        const HEALTH_INTERVAL = 2 * 60 * 1000; // 2 minutes
        
        if (timeSinceCheck >= HEALTH_INTERVAL) {
          checkHealth();
        }
      }
    }, 60000); // Check every minute
    
    return () => clearInterval(interval);
  }, [checkHealth, state.lastHealthCheck]);
```

### **Step 5: Agent Management**

```typescript
export const useOrchestrator = () => {
  // ... previous methods ...
  
  const refreshAgents = useCallback(async (forceRefresh = false): Promise<void> => {
    // Skip if recent refresh exists and not forcing
    const AGENTS_CACHE_MS = 60000; // 1 minute
    if (!forceRefresh && state.lastAgentsRefresh) {
      const timeSinceRefresh = Date.now() - state.lastAgentsRefresh.getTime();
      if (timeSinceRefresh < AGENTS_CACHE_MS && state.agents.length > 0) {
        return;
      }
    }
    
    safeSetState(prev => ({ ...prev, isRefreshing: true, error: null }));
    requestStartTimeRef.current = Date.now();
    
    try {
      const abortController = new AbortController();
      abortControllerRef.current = abortController;
      
      // First refresh agents on the orchestrator side
      await orchestratorApi.refreshAgents();
      
      // Then get the updated agent list
      const agents: AgentSummary[] = await orchestratorApi.getAgents();
      
      const responseTime = Date.now() - requestStartTimeRef.current;
      
      safeSetState(prev => ({
        ...prev,
        isRefreshing: false,
        agents,
        lastAgentsRefresh: new Date(),
        isHealthy: agents.length > 0 ? true : prev.isHealthy, // Update health if we got agents
        error: agents.length === 0 ? 'No agents discovered after refresh' : null,
      }));
      
      updateStats(true, responseTime);
      abortControllerRef.current = null;
      
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return;
      }
      
      handleError(error, 'refresh-agents');
    }
  }, [state.lastAgentsRefresh, state.agents.length, safeSetState, updateStats, handleError]);
  
  // Load initial agents
  useEffect(() => {
    const loadInitialAgents = async () => {
      try {
        const agents = await orchestratorApi.getAgents();
        safeSetState(prev => ({ 
          ...prev, 
          agents,
          lastAgentsRefresh: new Date(),
        }));
      } catch (error) {
        console.warn('Failed to load initial agents:', error);
        // Don't set error state - this is just initial loading
      }
    };
    
    loadInitialAgents();
  }, [safeSetState]);
```

### **Step 6: Message Processing**

```typescript
export const useOrchestrator = () => {
  // ... previous methods ...
  
  const processMessage = useCallback(async (query: string): Promise<ProcessResponse | null> => {
    if (!query.trim()) {
      safeSetState(prev => ({ ...prev, error: 'Please enter a message' }));
      return null;
    }
    
    safeSetState(prev => ({ 
      ...prev, 
      isLoading: true, 
      error: null,
      lastResponse: null,
    }));
    
    requestStartTimeRef.current = Date.now();
    
    try {
      const abortController = new AbortController();
      abortControllerRef.current = abortController;
      
      const response: ProcessResponse = await orchestratorApi.processMessage(query);
      const responseTime = Date.now() - requestStartTimeRef.current;
      
      safeSetState(prev => ({
        ...prev,
        isLoading: false,
        lastResponse: response,
      }));
      
      updateStats(true, responseTime);
      abortControllerRef.current = null;
      
      return response;
      
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return null;
      }
      
      handleError(error, 'process-message');
      return null;
    }
  }, [safeSetState, updateStats, handleError]);
  
  // Batch process multiple messages (useful for testing)
  const processMessages = useCallback(async (queries: string[]): Promise<ProcessResponse[]> => {
    const results: ProcessResponse[] = [];
    
    for (const query of queries) {
      const response = await processMessage(query);
      if (response) {
        results.push(response);
      }
    }
    
    return results;
  }, [processMessage]);
```

### **Step 7: Utility Functions and Cache Management**

```typescript
export const useOrchestrator = () => {
  // ... previous methods ...
  
  const clearError = useCallback(() => {
    safeSetState(prev => ({ ...prev, error: null, lastError: null }));
  }, [safeSetState]);
  
  const abortCurrentRequest = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      
      safeSetState(prev => ({
        ...prev,
        isLoading: false,
        isRefreshing: false,
        error: 'Request cancelled',
      }));
    }
  }, [safeSetState]);
  
  // Reset all state (useful for testing or user-initiated reset)
  const resetState = useCallback(() => {
    abortCurrentRequest();
    setState(initialOrchestratorState);
  }, [abortCurrentRequest]);
  
  // Get agents filtered by capability
  const getAgentsByCapability = useCallback((capability: string): AgentSummary[] => {
    return state.agents.filter(agent => 
      agent.capabilities.some(cap => 
        cap.tags.includes(capability.toLowerCase()) ||
        cap.name.toLowerCase().includes(capability.toLowerCase())
      )
    );
  }, [state.agents]);
  
  // Check if a specific agent is available
  const isAgentAvailable = useCallback((agentId: string): boolean => {
    return state.agents.some(agent => 
      agent.agent_id === agentId && agent.status === 'healthy'
    );
  }, [state.agents]);
  
  // Get system health summary
  const getHealthSummary = useCallback(() => {
    const healthyAgents = state.agents.filter(agent => agent.status === 'healthy');
    const totalCapabilities = state.agents.reduce((sum, agent) => sum + agent.capabilities.length, 0);
    
    return {
      isHealthy: state.isHealthy,
      totalAgents: state.agents.length,
      healthyAgents: healthyAgents.length,
      totalCapabilities,
      lastHealthCheck: state.lastHealthCheck,
      uptime: state.lastHealthCheck ? Date.now() - state.lastHealthCheck.getTime() : null,
    };
  }, [state.isHealthy, state.agents, state.lastHealthCheck]);
```

### **Step 8: Hook API Export**

```typescript
export const useOrchestrator = () => {
  // ... all previous implementation ...
  
  return {
    // State
    ...state,
    
    // Actions
    processMessage,
    processMessages,
    checkHealth,
    refreshAgents,
    clearError,
    abortCurrentRequest,
    resetState,
    
    // Computed Values
    isConnected: state.isHealthy === true && !state.error,
    hasAgents: state.agents.length > 0,
    healthyAgentCount: state.agents.filter(a => a.status === 'healthy').length,
    errorRate: state.stats.totalRequests > 0 
      ? state.stats.failedRequests / state.stats.totalRequests 
      : 0,
    
    // Utility Functions
    getAgentsByCapability,
    isAgentAvailable,
    getHealthSummary,
    
    // Cache Status
    isHealthCacheValid: state.lastHealthCheck 
      ? Date.now() - state.lastHealthCheck.getTime() < 30000 
      : false,
    isAgentsCacheValid: state.lastAgentsRefresh 
      ? Date.now() - state.lastAgentsRefresh.getTime() < 60000 
      : false,
  };
};
```

## 🧪 **Testing Custom Hooks**

### **Unit Testing with React Testing Library**

```typescript
// src/hooks/__tests__/useOrchestrator.test.ts
import { renderHook, act } from '@testing-library/react';
import { useOrchestrator } from '../useOrchestrator';

// Mock the orchestrator API
jest.mock('../services/orchestratorApi');

const mockOrchestratorApi = jest.mocked(orchestratorApi);

describe('useOrchestrator', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.clearAllTimers();
    jest.useFakeTimers();
  });
  
  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });
  
  it('should initialize with correct default state', () => {
    const { result } = renderHook(() => useOrchestrator());
    
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isHealthy).toBe(null);
    expect(result.current.agents).toEqual([]);
    expect(result.current.error).toBe(null);
    expect(result.current.stats.totalRequests).toBe(0);
  });
  
  it('should perform health check on mount', async () => {
    mockOrchestratorApi.checkHealth.mockResolvedValueOnce({
      status: 'healthy',
      agents_discovered: 2,
      timestamp: new Date().toISOString(),
    });
    
    const { result, waitForNextUpdate } = renderHook(() => useOrchestrator());
    
    // Health check should start automatically
    expect(result.current.isLoading).toBe(true);
    
    await waitForNextUpdate();
    
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isHealthy).toBe(true);
    expect(mockOrchestratorApi.checkHealth).toHaveBeenCalledTimes(1);
  });
  
  it('should handle health check failure', async () => {
    mockOrchestratorApi.checkHealth.mockRejectedValueOnce(new Error('Connection failed'));
    
    const { result, waitForNextUpdate } = renderHook(() => useOrchestrator());
    
    await waitForNextUpdate();
    
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isHealthy).toBe(null);
    expect(result.current.error).toContain('check your internet connection');
  });
  
  it('should process messages successfully', async () => {
    const mockResponse = {
      request_id: 'test-123',
      agent_id: 'test-agent',
      agent_name: 'Test Agent',
      protocol: 'test',
      content: 'Test response',
      confidence: 0.95,
      success: true,
      duration_ms: 100,
      timestamp: new Date().toISOString(),
    };
    
    mockOrchestratorApi.processMessage.mockResolvedValueOnce(mockResponse);
    
    const { result } = renderHook(() => useOrchestrator());
    
    await act(async () => {
      const response = await result.current.processMessage('test query');
      expect(response).toEqual(mockResponse);
    });
    
    expect(result.current.lastResponse).toEqual(mockResponse);
    expect(result.current.stats.successfulRequests).toBe(1);
    expect(result.current.stats.totalRequests).toBe(1);
  });
  
  it('should handle message processing errors', async () => {
    mockOrchestratorApi.processMessage.mockRejectedValueOnce(new Error('Processing failed'));
    
    const { result } = renderHook(() => useOrchestrator());
    
    await act(async () => {
      const response = await result.current.processMessage('test query');
      expect(response).toBeNull();
    });
    
    expect(result.current.error).toContain('Failed to process your message');
    expect(result.current.stats.failedRequests).toBe(1);
    expect(result.current.errorRate).toBe(1);
  });
  
  it('should refresh agents', async () => {
    const mockAgents = [
      {
        agent_id: 'agent-1',
        name: 'Test Agent 1',
        protocol: 'test',
        endpoint: 'http://test-1',
        status: 'healthy',
        capabilities: [{ name: 'test', tags: ['test'] }],
      },
    ];
    
    mockOrchestratorApi.refreshAgents.mockResolvedValueOnce(undefined);
    mockOrchestratorApi.getAgents.mockResolvedValueOnce(mockAgents);
    
    const { result } = renderHook(() => useOrchestrator());
    
    await act(async () => {
      await result.current.refreshAgents(true);
    });
    
    expect(result.current.agents).toEqual(mockAgents);
    expect(result.current.hasAgents).toBe(true);
    expect(result.current.healthyAgentCount).toBe(1);
  });
  
  it('should filter agents by capability', async () => {
    const mockAgents = [
      {
        agent_id: 'math-agent',
        name: 'Math Agent',
        protocol: 'a2a',
        endpoint: 'http://math',
        status: 'healthy',
        capabilities: [{ name: 'math', tags: ['math', 'calculation'] }],
      },
      {
        agent_id: 'hello-agent',
        name: 'Hello Agent',
        protocol: 'acp',
        endpoint: 'http://hello',
        status: 'healthy',
        capabilities: [{ name: 'greeting', tags: ['hello', 'greeting'] }],
      },
    ];
    
    // Setup initial state with agents
    mockOrchestratorApi.getAgents.mockResolvedValueOnce(mockAgents);
    const { result, waitForNextUpdate } = renderHook(() => useOrchestrator());
    await waitForNextUpdate();
    
    // Test capability filtering
    const mathAgents = result.current.getAgentsByCapability('math');
    const greetingAgents = result.current.getAgentsByCapability('greeting');
    
    expect(mathAgents).toHaveLength(1);
    expect(mathAgents[0].agent_id).toBe('math-agent');
    expect(greetingAgents).toHaveLength(1);
    expect(greetingAgents[0].agent_id).toBe('hello-agent');
  });
  
  it('should cleanup on unmount', () => {
    const { unmount } = renderHook(() => useOrchestrator());
    
    // Should not throw or cause memory leaks
    unmount();
  });
  
  it('should cache health checks', async () => {
    mockOrchestratorApi.checkHealth.mockResolvedValue({
      status: 'healthy',
      agents_discovered: 2,
      timestamp: new Date().toISOString(),
    });
    
    const { result, waitForNextUpdate } = renderHook(() => useOrchestrator());
    
    // Initial health check
    await waitForNextUpdate();
    expect(mockOrchestratorApi.checkHealth).toHaveBeenCalledTimes(1);
    
    // Second health check should be cached
    await act(async () => {
      const isHealthy = await result.current.checkHealth(false);
      expect(isHealthy).toBe(true);
    });
    
    // Should still be only 1 call due to caching
    expect(mockOrchestratorApi.checkHealth).toHaveBeenCalledTimes(1);
    
    // Force refresh should bypass cache
    await act(async () => {
      await result.current.checkHealth(true);
    });
    
    expect(mockOrchestratorApi.checkHealth).toHaveBeenCalledTimes(2);
  });
});
```

### **Integration Testing**

```typescript
// src/hooks/__tests__/useOrchestrator.integration.test.ts
import { renderHook, act } from '@testing-library/react';
import { useOrchestrator } from '../useOrchestrator';

describe('useOrchestrator Integration', () => {
  const isRealApiTest = process.env.TEST_WITH_REAL_API === 'true';
  
  it.skipIf(!isRealApiTest)('should connect to real orchestrator', async () => {
    const { result, waitForNextUpdate } = renderHook(() => useOrchestrator());
    
    // Wait for initial health check
    await waitForNextUpdate();
    
    expect(result.current.isHealthy).toBe(true);
    expect(result.current.agents.length).toBeGreaterThan(0);
    expect(result.current.isConnected).toBe(true);
  });
  
  it.skipIf(!isRealApiTest)('should process real messages', async () => {
    const { result, waitForNextUpdate } = renderHook(() => useOrchestrator());
    
    await waitForNextUpdate(); // Wait for initial setup
    
    await act(async () => {
      const response = await result.current.processMessage('Hello there!');
      expect(response).toBeTruthy();
      expect(response?.content).toBeTruthy();
      expect(response?.agent_name).toBeTruthy();
    });
    
    expect(result.current.stats.successfulRequests).toBe(1);
    expect(result.current.errorRate).toBe(0);
  }, 10000);
  
  it.skipIf(!isRealApiTest)('should refresh agents from real orchestrator', async () => {
    const { result, waitForNextUpdate } = renderHook(() => useOrchestrator());
    
    await waitForNextUpdate();
    
    const initialAgentCount = result.current.agents.length;
    
    await act(async () => {
      await result.current.refreshAgents(true);
    });
    
    // Should have agents after refresh
    expect(result.current.agents.length).toBeGreaterThanOrEqual(initialAgentCount);
    expect(result.current.healthyAgentCount).toBeGreaterThan(0);
  });
});
```

## 🎯 **Hook Usage Patterns**

### **Basic Usage in Components**

```typescript
// Simple component usage
const HealthDashboard: React.FC = () => {
  const {
    isHealthy,
    isLoading,
    error,
    agents,
    checkHealth,
    getHealthSummary,
  } = useOrchestrator();
  
  const healthSummary = getHealthSummary();
  
  if (isLoading) {
    return <div>Checking system health...</div>;
  }
  
  if (error) {
    return (
      <div className="error">
        <p>Error: {error}</p>
        <button onClick={() => checkHealth(true)}>
          Retry Health Check
        </button>
      </div>
    );
  }
  
  return (
    <div className="health-dashboard">
      <h2>System Health</h2>
      <div className={`status ${isHealthy ? 'healthy' : 'unhealthy'}`}>
        Status: {isHealthy ? '✅ Healthy' : '❌ Unhealthy'}
      </div>
      
      <div className="metrics">
        <p>Total Agents: {healthSummary.totalAgents}</p>
        <p>Healthy Agents: {healthSummary.healthyAgents}</p>
        <p>Capabilities: {healthSummary.totalCapabilities}</p>
      </div>
      
      <div className="agents">
        {agents.map(agent => (
          <div key={agent.agent_id} className="agent">
            <strong>{agent.name}</strong>
            <span className="protocol">{agent.protocol}</span>
            <span className={`status ${agent.status}`}>{agent.status}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
```

### **Advanced Usage with Error Boundaries**

```typescript
// Component with comprehensive error handling
const AgentQueryInterface: React.FC = () => {
  const {
    processMessage,
    isLoading,
    lastResponse,
    error,
    clearError,
    stats,
    abortCurrentRequest,
  } = useOrchestrator();
  
  const [query, setQuery] = useState('');
  const [responses, setResponses] = useState<ProcessResponse[]>([]);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    const response = await processMessage(query);
    if (response) {
      setResponses(prev => [...prev, response]);
      setQuery('');
    }
  };
  
  const handleCancel = () => {
    abortCurrentRequest();
  };
  
  return (
    <div className="query-interface">
      <form onSubmit={handleSubmit}>
        <div className="input-group">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your query..."
            disabled={isLoading}
          />
          
          <button type="submit" disabled={isLoading || !query.trim()}>
            {isLoading ? 'Processing...' : 'Send'}
          </button>
          
          {isLoading && (
            <button type="button" onClick={handleCancel}>
              Cancel
            </button>
          )}
        </div>
        
        {error && (
          <div className="error-message">
            <p>{error}</p>
            <button onClick={clearError}>Dismiss</button>
          </div>
        )}
      </form>
      
      <div className="stats">
        <p>Requests: {stats.totalRequests}</p>
        <p>Success Rate: {((1 - stats.failedRequests / stats.totalRequests) * 100).toFixed(1)}%</p>
        <p>Avg Response Time: {stats.averageResponseTime.toFixed(0)}ms</p>
      </div>
      
      <div className="responses">
        {responses.map(response => (
          <div key={response.request_id} className="response">
            <div className="header">
              <strong>{response.agent_name}</strong>
              <span className="protocol">{response.protocol}</span>
              <span className="confidence">{Math.round(response.confidence * 100)}%</span>
            </div>
            <div className="content">{response.content}</div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

## 🎯 **Key Takeaways**

1. **Encapsulate complexity in hooks** - Keep components simple and focused
2. **Handle all async states** - loading, success, error, and cleanup
3. **Implement proper cancellation** - Use AbortController for cleanup
4. **Cache when appropriate** - Don't spam APIs with repeated requests
5. **Provide useful computed values** - Make the hook API convenient to use
6. **Track metrics and statistics** - Monitor hook performance and usage
7. **Test thoroughly** - Both unit and integration tests are crucial

## 📋 **Next Steps**

In the next tutorial, we'll explore:
- **Advanced Hook Patterns**: Hook composition and custom hook libraries
- **State Synchronization**: Keeping multiple hooks in sync
- **Performance Optimization**: Avoiding unnecessary re-renders
- **Error Recovery Strategies**: Automatic retry and fallback patterns

---

**Next**: [Advanced Hook Patterns](../advanced-features/03-advanced-hook-patterns.md) - Hook Composition & Libraries

**Previous**: [02-service-layer-architecture.md](./02-service-layer-architecture.md)