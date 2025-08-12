import { useState, useCallback, useEffect, useRef } from 'react';
import { orchestratorApi, type ProcessResponse, type AgentSummary } from '../services/orchestratorApi.ts';
import { streamingApi, type RoutingEvent, type CompletedEvent } from '../services/streamingApi.ts';

export interface StreamingState {
  isStreaming: boolean;
  currentChunk: string;
  accumulatedResponse: string;
  routingInfo: {
    agentId?: string;
    agentName?: string;
    protocol?: string;
    confidence?: number;
    reasoning?: string;
  } | null;
  streamPhase: 'idle' | 'routing' | 'executing' | 'streaming' | 'completed' | 'error';
}

export interface UseStreamingOrchestratorReturn {
  // State
  isHealthy: boolean;
  isLoading: boolean;
  error: string | null;
  agents: AgentSummary[];
  streamingState: StreamingState;
  
  // Actions
  processMessageStream: (query: string) => Promise<ProcessResponse | null>;
  processMessage: (query: string) => Promise<ProcessResponse | null>;
  checkHealth: () => Promise<void>;
  refreshAgents: () => Promise<void>;
  clearError: () => void;
  abortStream: () => void;
}

export function useStreamingOrchestrator(): UseStreamingOrchestratorReturn {
  const [isHealthy, setIsHealthy] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [streamingState, setStreamingState] = useState<StreamingState>({
    isStreaming: false,
    currentChunk: '',
    accumulatedResponse: '',
    routingInfo: null,
    streamPhase: 'idle',
  });

  const responseRef = useRef<ProcessResponse | null>(null);
  const routingDataRef = useRef<RoutingEvent | null>(null);

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

  const processMessageStream = useCallback(async (query: string): Promise<ProcessResponse | null> => {
    setIsLoading(true);
    setError(null);
    setStreamingState({
      isStreaming: true,
      currentChunk: '',
      accumulatedResponse: '',
      routingInfo: null,
      streamPhase: 'routing',
    });
    responseRef.current = null;
    routingDataRef.current = null;

    try {
      let accumulatedText = '';
      
      await streamingApi.processMessageStream(
        query,
        {
          onRequestReceived: () => {
            setStreamingState(prev => ({ ...prev, streamPhase: 'routing' }));
          },
          
          onRoutingStarted: () => {
            setStreamingState(prev => ({ ...prev, streamPhase: 'routing' }));
          },
          
          onRoutingCompleted: (data: RoutingEvent) => {
            routingDataRef.current = data; // Store routing data in ref
            setStreamingState(prev => ({
              ...prev,
              streamPhase: 'executing',
              routingInfo: {
                agentId: data.agent_id || undefined,
                agentName: data.agent_name || undefined,
                protocol: data.protocol || undefined,
                confidence: data.confidence,
                reasoning: data.reasoning,
              },
            }));
          },
          
          onAgentExecutionStarted: (_agentId: string) => {
            setStreamingState(prev => ({ ...prev, streamPhase: 'executing' }));
          },
          
          onResponseChunk: (chunk: string) => {
            accumulatedText += chunk;
            setStreamingState(prev => ({
              ...prev,
              streamPhase: 'streaming',
              currentChunk: chunk,
              accumulatedResponse: accumulatedText,
            }));
          },
          
          onCompleted: (data: CompletedEvent) => {
            // Create ProcessResponse from completed event
            const response: ProcessResponse = {
              request_id: data.response_data?.request_id || 'stream-' + Date.now(),
              agent_id: data.agent_id,
              protocol: data.protocol,
              response_data: data.response_data,
              duration_ms: 0, // Not tracked in streaming
              success: true,
              error: null,
              metadata: {
                routing_decision: {
                  selected_agent: {
                    agent_id: data.agent_id,
                    name: data.agent_name,
                  },
                  confidence: data.confidence,
                  reasoning: routingDataRef.current?.reasoning,
                },
              },
              timestamp: data.timestamp,
              content: orchestratorApi.extractResponseContent({
                response_data: data.response_data,
                protocol: data.protocol,
              }),
              agent_name: data.agent_name,
              confidence: data.confidence,
              reasoning: routingDataRef.current?.reasoning,
            };
            
            responseRef.current = response;
            
            setStreamingState(prev => ({
              ...prev,
              isStreaming: false,
              streamPhase: 'completed',
            }));
            
            // Refresh agents if we got agent info
            if (data.agent_id) {
              loadAgents();
            }
          },
          
          onError: (errorMessage: string) => {
            setError(errorMessage);
            setStreamingState(prev => ({
              ...prev,
              isStreaming: false,
              streamPhase: 'error',
            }));
          },
        },
        undefined // context
      );

      return responseRef.current;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to process message';
      setError(errorMessage);
      setStreamingState(prev => ({
        ...prev,
        isStreaming: false,
        streamPhase: 'error',
      }));
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [loadAgents]);

  const processMessage = useCallback(async (query: string): Promise<ProcessResponse | null> => {
    // Non-streaming fallback
    setIsLoading(true);
    setError(null);

    try {
      const response = await orchestratorApi.processMessage(query);
      
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
  }, [loadAgents]);

  const refreshAgents = useCallback(async () => {
    try {
      await orchestratorApi.refreshAgents();
      await loadAgents();
    } catch (err) {
      console.error('Failed to refresh agents:', err);
    }
  }, [loadAgents]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const abortStream = useCallback(() => {
    streamingApi.abort();
    setStreamingState({
      isStreaming: false,
      currentChunk: '',
      accumulatedResponse: '',
      routingInfo: null,
      streamPhase: 'idle',
    });
    setIsLoading(false);
  }, []);

  return {
    isHealthy,
    isLoading,
    error,
    agents,
    streamingState,
    processMessageStream,
    processMessage,
    checkHealth,
    refreshAgents,
    clearError,
    abortStream,
  };
}