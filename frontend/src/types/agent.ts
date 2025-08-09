export interface AgentCapability {
  name: string;
  description?: string;
}

export interface Agent {
  agent_id: string;
  name: string;
  protocol: 'acp' | 'a2a' | 'mcp' | 'custom';
  status: 'healthy' | 'degraded' | 'unhealthy';
  capabilities: string[];
  endpoint: string;
  last_seen: Date;
  description?: string;
}

export interface RoutingDecision {
  selected_agent: Agent | null;
  confidence: number;
  reasoning: string;
  fallback_agents?: Agent[];
}