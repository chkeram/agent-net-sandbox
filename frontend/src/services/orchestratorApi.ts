import type { Message } from '../types/chat.ts';
import type { Agent, RoutingDecision } from '../types/agent.ts';

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8004';

// API response types
export interface ProcessResponse {
  request_id: string;
  agent_id?: string;
  protocol?: string;
  response_data?: {
    message?: string;
    query?: string;
    agent_id?: string;
    protocol?: string;
    timestamp?: string;
    simulated?: boolean;
    
    // A2A Protocol response structure
    raw_response?: {
      parts?: Array<{
        kind?: string;
        text?: string;
      }>;
    };
    
    // ACP Protocol response structure
    output?: {
      greeting?: string;
      timestamp?: string;
      agent_id?: string;
      [key: string]: any; // Allow other ACP output fields
    };
    status?: string;
  };
  duration_ms?: number;
  success: boolean;
  error?: string | null;
  metadata?: {
    routing_decision?: {
      selected_agent?: any;
      reasoning?: string;
      confidence?: number;
    };
    agent_protocol?: string;
    agent_capabilities?: string[];
  };
  timestamp?: string;
  
  // Computed/mapped fields for compatibility
  content?: string;
  agent_name?: string;
  confidence?: number;
  reasoning?: string;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  timestamp: string;
  services: {
    orchestrator: string;
    discovery_service: string;
    llm_provider: string;
  };
  details: {
    orchestrator_healthy: boolean;
    discovery_service_healthy: boolean;
    available_agents: number;
  };
}

export interface AgentSummary {
  agent_id: string;
  name: string;
  protocol: string;
  status: string;
  capabilities: string[];
  endpoint: string;
  last_seen: string;
}

// API client class
export class OrchestratorAPI {
  private baseUrl: string;
  private headers: HeadersInit;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Content-Type': 'application/json',
    };
  }

  // Health check
  async checkHealth(): Promise<HealthResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
        headers: this.headers,
      });

      if (!response.ok) {
        throw new Error(`Health check failed: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Health check error:', error);
      throw error;
    }
  }

  // Process a message through the orchestrator
  async processMessage(query: string, context?: any): Promise<ProcessResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/process`, {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({
          query,
          context,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Request failed: ${response.status}`);
      }

      const data = await response.json();
      
      // Extract clean content using protocol-aware parsing
      const content = this._extractResponseContent(data);
      
      // Map the response to include computed fields for easier access
      return {
        ...data,
        content,
        agent_name: data.metadata?.routing_decision?.selected_agent?.name || data.agent_id,
        confidence: data.metadata?.routing_decision?.confidence,
        reasoning: data.metadata?.routing_decision?.reasoning,
      };
    } catch (error) {
      console.error('Process message error:', error);
      throw error;
    }
  }

  // Get routing decision without executing
  async getRoutingDecision(query: string): Promise<RoutingDecision> {
    try {
      const response = await fetch(`${this.baseUrl}/route`, {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        throw new Error(`Routing failed: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Routing decision error:', error);
      throw error;
    }
  }

  // Get all discovered agents
  async getAgents(protocol?: string, capability?: string): Promise<AgentSummary[]> {
    try {
      const params = new URLSearchParams();
      if (protocol) params.append('protocol', protocol);
      if (capability) params.append('capability', capability);

      const url = `${this.baseUrl}/agents${params.toString() ? '?' + params.toString() : ''}`;
      const response = await fetch(url, {
        method: 'GET',
        headers: this.headers,
      });

      if (!response.ok) {
        throw new Error(`Failed to get agents: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Get agents error:', error);
      throw error;
    }
  }

  // Get specific agent details
  async getAgent(agentId: string): Promise<Agent> {
    try {
      const response = await fetch(`${this.baseUrl}/agents/${agentId}`, {
        method: 'GET',
        headers: this.headers,
      });

      if (!response.ok) {
        throw new Error(`Failed to get agent: ${response.status}`);
      }

      const data = await response.json();
      return {
        ...data,
        last_seen: new Date(data.last_seen),
      };
    } catch (error) {
      console.error('Get agent error:', error);
      throw error;
    }
  }

  // Refresh agent discovery
  async refreshAgents(): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/agents/refresh`, {
        method: 'POST',
        headers: this.headers,
      });

      if (!response.ok) {
        throw new Error(`Failed to refresh agents: ${response.status}`);
      }
    } catch (error) {
      console.error('Refresh agents error:', error);
      throw error;
    }
  }

  // Get orchestration metrics
  async getMetrics(): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/metrics`, {
        method: 'GET',
        headers: this.headers,
      });

      if (!response.ok) {
        throw new Error(`Failed to get metrics: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Get metrics error:', error);
      throw error;
    }
  }

  // Private method to extract clean content from protocol-specific responses
  private _extractResponseContent(data: any): string {
    const responseData = data.response_data;
    
    if (!responseData) {
      return 'No response received';
    }

    // Protocol-specific extraction based on detected protocol
    const protocol = data.protocol?.toLowerCase() || data.metadata?.agent_protocol?.toLowerCase();
    
    try {
      // A2A Protocol: Extract from parts array
      if (protocol === 'a2a' && responseData.raw_response?.parts?.length > 0) {
        const textParts = responseData.raw_response.parts
          .filter((part: any) => part.kind === 'text' || !part.kind) // Include parts without kind (default to text)
          .map((part: any) => part.text)
          .filter(Boolean); // Remove empty/null values
        
        if (textParts.length > 0) {
          return textParts.join(' ').trim();
        }
      }
      
      // ACP Protocol: Extract from output object
      if (protocol === 'acp' && responseData.output) {
        // Try common ACP output fields
        const greeting = responseData.output.greeting;
        if (greeting && typeof greeting === 'string') {
          return greeting.trim();
        }
        
        // Look for other string fields in output
        for (const [key, value] of Object.entries(responseData.output)) {
          if (typeof value === 'string' && key !== 'timestamp' && key !== 'agent_id') {
            return (value as string).trim();
          }
        }
      }
      
      // Fallback to message field for any protocol
      if (responseData.message && typeof responseData.message === 'string') {
        return responseData.message.trim();
      }
      
    } catch (error) {
      console.warn('Error during protocol-specific content extraction:', error);
    }
    
    // Final fallback
    return 'No response content available';
  }
}

// Create singleton instance
export const orchestratorApi = new OrchestratorAPI();