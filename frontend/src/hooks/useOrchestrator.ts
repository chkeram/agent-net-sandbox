import { useState, useCallback, useEffect } from 'react';
import { orchestratorApi } from '../services/orchestratorApi.ts';
import type { ProcessResponse, HealthResponse, AgentSummary } from '../services/orchestratorApi.ts';
import type { Message } from '../types/chat.ts';

export interface UseOrchestratorReturn {
  // State
  isHealthy: boolean;
  isLoading: boolean;
  error: string | null;
  agents: AgentSummary[];
  
  // Actions
  processMessage: (query: string) => Promise<ProcessResponse | null>;
  checkHealth: () => Promise<void>;
  refreshAgents: () => Promise<void>;
  clearError: () => void;
}

export function useOrchestrator(): UseOrchestratorReturn {
  const [isHealthy, setIsHealthy] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agents, setAgents] = useState<AgentSummary[]>([]);

  // Check health on mount
  useEffect(() => {
    checkHealth();
    loadAgents();
  }, []);

  const checkHealth = useCallback(async () => {
    try {
      const health = await orchestratorApi.checkHealth();
      setIsHealthy(health.status === 'healthy');
      setError(null);
    } catch (err) {
      setIsHealthy(false);
      setError('Orchestrator is not available. Please ensure it is running.');
      console.error('Health check failed:', err);
    }
  }, []);

  const loadAgents = useCallback(async () => {
    try {
      const agentList = await orchestratorApi.getAgents();
      setAgents(agentList);
    } catch (err) {
      console.error('Failed to load agents:', err);
    }
  }, []);

  const processMessage = useCallback(async (query: string): Promise<ProcessResponse | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await orchestratorApi.processMessage(query);
      
      // If we got agent info, refresh the agents list
      if (response.agent_id) {
        loadAgents();
      }

      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to process message';
      setError(errorMessage);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const refreshAgents = useCallback(async () => {
    try {
      await orchestratorApi.refreshAgents();
      await loadAgents();
    } catch (err) {
      console.error('Failed to refresh agents:', err);
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    isHealthy,
    isLoading,
    error,
    agents,
    processMessage,
    checkHealth,
    refreshAgents,
    clearError,
  };
}