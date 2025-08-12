// Streaming API for orchestrator
import { orchestratorApi } from './orchestratorApi.ts';

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8004';

// SSE Event types
export interface SSEEvent {
  event: 'request_received' | 'routing_started' | 'routing_completed' | 
         'agent_execution_started' | 'response_chunk' | 'completed' | 'error';
  timestamp: string;
  [key: string]: any;
}

export interface RoutingEvent extends SSEEvent {
  event: 'routing_completed';
  agent_id: string | null;
  agent_name: string | null;
  protocol: string | null;
  confidence: number;
  reasoning: string;
}

export interface ResponseChunkEvent extends SSEEvent {
  event: 'response_chunk';
  chunk?: string; // For backwards compatibility
  response_data?: any; // Raw response data from agent
  protocol?: string; // Protocol type for parsing
}

export interface CompletedEvent extends SSEEvent {
  event: 'completed';
  agent_id: string;
  agent_name: string;
  protocol: string;
  confidence: number;
  response_data: any;
}

export interface StreamCallbacks {
  onRequestReceived?: () => void;
  onRoutingStarted?: () => void;
  onRoutingCompleted?: (data: RoutingEvent) => void;
  onAgentExecutionStarted?: (agentId: string) => void;
  onResponseChunk?: (chunk: string) => void;
  onCompleted?: (data: CompletedEvent) => void;
  onError?: (error: string) => void;
}

export class StreamingOrchestratorAPI {
  private baseUrl: string;
  private abortController: AbortController | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async processMessageStream(
    query: string,
    callbacks: StreamCallbacks,
    context?: any
  ): Promise<void> {
    // Abort any existing stream
    this.abort();

    // Create new abort controller
    this.abortController = new AbortController();

    try {
      const response = await fetch(`${this.baseUrl}/process/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({
          query,
          context,
        }),
        signal: this.abortController.signal,
      });

      if (!response.ok) {
        const errorText = await response.text().catch(() => '');
        console.error('StreamingAPI: Error response', errorText);
        throw new Error(errorText || `Request failed: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        
        // Keep the last incomplete line in the buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            
            // Skip empty data or [DONE] signal
            if (!data || data === '[DONE]') continue;

            try {
              const event = JSON.parse(data) as SSEEvent;
              this.handleEvent(event, callbacks);
            } catch (e) {
              console.warn('Failed to parse SSE event:', data, e);
            }
          }
        }
      }
    } catch (error) {
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          // Stream was intentionally aborted
          return;
        }
        callbacks.onError?.(error.message);
      }
      throw error;
    } finally {
      this.abortController = null;
    }
  }

  private handleEvent(event: SSEEvent, callbacks: StreamCallbacks) {
    switch (event.event) {
      case 'request_received':
        callbacks.onRequestReceived?.();
        break;
      
      case 'routing_started':
        callbacks.onRoutingStarted?.();
        break;
      
      case 'routing_completed':
        callbacks.onRoutingCompleted?.(event as RoutingEvent);
        break;
      
      case 'agent_execution_started':
        callbacks.onAgentExecutionStarted?.(event.agent_id);
        break;
      
      case 'response_chunk':
        const chunkEvent = event as ResponseChunkEvent;
        
        if (chunkEvent.chunk) {
          // Backwards compatibility: pre-extracted chunk
          callbacks.onResponseChunk?.(chunkEvent.chunk);
        } else if (chunkEvent.response_data && chunkEvent.protocol) {
          // New format: extract content using protocol-aware parsing
          try {
            const extractedContent = orchestratorApi.extractResponseContent({
              response_data: chunkEvent.response_data,
              protocol: chunkEvent.protocol,
            });
            callbacks.onResponseChunk?.(extractedContent);
          } catch (error) {
            console.warn('Failed to extract content from response chunk:', error);
            callbacks.onResponseChunk?.('Error processing response');
          }
        }
        break;
      
      case 'completed':
        callbacks.onCompleted?.(event as CompletedEvent);
        break;
      
      case 'error':
        callbacks.onError?.(event.error || 'Unknown error');
        break;
      
      default:
        console.warn('Unknown SSE event:', event);
    }
  }

  abort() {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }
}

// Create singleton instance
export const streamingApi = new StreamingOrchestratorAPI();