"""Pydantic AI Agent for orchestrator with multi-LLM support"""

import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

import structlog
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import Model, infer_model

from .config import get_settings
from .models import (
    RoutingRequest, RoutingDecision, AgentResponse, 
    DiscoveredAgent, AgentCapability, ProtocolType,
    OrchestrationMetrics, LLMProvider
)
from .discovery import UnifiedDiscoveryService

logger = structlog.get_logger(__name__)


class OrchestratorContext:
    """Context passed to Pydantic AI agent containing orchestrator state"""
    
    def __init__(
        self,
        discovery_service: UnifiedDiscoveryService,
        request: RoutingRequest
    ):
        self.discovery_service = discovery_service
        self.request = request
        self.available_agents: List[DiscoveredAgent] = []
        self.routing_start_time = datetime.utcnow()


class OrchestratorAgent:
    """Main orchestrator agent using Pydantic AI for intelligent routing"""
    
    def __init__(self, discovery_service: UnifiedDiscoveryService):
        self.discovery_service = discovery_service
        self.settings = get_settings()
        self.metrics = OrchestrationMetrics()
        
        # Initialize the AI model based on configuration
        self.model = self._create_model()
        
        # Create the Pydantic AI agent
        self.agent = Agent(
            model=self.model,
            system_prompt=self._get_system_prompt(),
            deps_type=OrchestratorContext,
            output_type=RoutingDecision
        )
        
        # Register agent tools/functions
        self._register_agent_functions()
        
        logger.info(
            "Orchestrator agent initialized",
            llm_provider=self.settings.llm_provider,
            model_name=self.model.name if hasattr(self.model, 'name') else str(type(self.model))
        )
    
    def _create_model(self) -> Model:
        """Create appropriate AI model based on configuration"""
        import os
        
        provider = self.settings.llm_provider
        
        if provider == LLMProvider.OPENAI:
            if not self.settings.openai_api_key:
                raise ValueError("OpenAI API key is required when using OpenAI provider")
            
            # Set environment variable temporarily for model creation
            old_key = os.environ.get('OPENAI_API_KEY')
            os.environ['OPENAI_API_KEY'] = self.settings.openai_api_key
            try:
                model = infer_model('openai:gpt-4o')
            finally:
                if old_key is not None:
                    os.environ['OPENAI_API_KEY'] = old_key
                else:
                    os.environ.pop('OPENAI_API_KEY', None)
            return model
        
        elif provider == LLMProvider.ANTHROPIC:
            if not self.settings.anthropic_api_key:
                raise ValueError("Anthropic API key is required when using Anthropic provider")
            
            # Set environment variable temporarily for model creation
            old_key = os.environ.get('ANTHROPIC_API_KEY')
            os.environ['ANTHROPIC_API_KEY'] = self.settings.anthropic_api_key
            try:
                model = infer_model('anthropic:claude-3-5-sonnet-20241022')
            finally:
                if old_key is not None:
                    os.environ['ANTHROPIC_API_KEY'] = old_key
                else:
                    os.environ.pop('ANTHROPIC_API_KEY', None)
            return model
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the orchestrator agent"""
        return """
You are an intelligent agent orchestrator responsible for routing user queries to the most appropriate specialized agents.

Your role is to:
1. Analyze incoming user queries to understand their intent and requirements
2. Evaluate available specialized agents and their capabilities 
3. Select the best agent(s) to handle each query
4. Make routing decisions with confidence scores
5. Provide clear reasoning for your choices

You have access to a discovery service that maintains a registry of available agents across multiple protocols (ACP, A2A, MCP). Each agent has:
- Capabilities: What the agent can do (e.g., "greeting", "math", "weather")
- Protocol: Communication protocol (ACP, A2A, MCP)
- Health status: Whether the agent is currently available
- Metadata: Additional information about the agent

Guidelines for routing decisions:
- Always prefer healthy agents over degraded/unhealthy ones
- Match query intent to agent capabilities as closely as possible
- Consider agent specialization (prefer specialized agents over general ones)
- For complex queries, consider if multiple agents might be needed
- Provide confidence scores between 0.0 and 1.0
- Include clear reasoning for your decisions

Be concise but thorough in your analysis. Focus on making the best routing decision for the user's needs.
        """.strip()
    
    def _register_agent_functions(self):
        """Register tools/functions available to the AI agent"""
        
        @self.agent.tool
        async def get_available_agents(ctx: RunContext[OrchestratorContext]) -> List[Dict[str, Any]]:
            """Get list of currently available and healthy agents"""
            agents = await ctx.deps.discovery_service.get_healthy_agents()
            ctx.deps.available_agents = agents
            
            return [
                {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "protocol": agent.protocol.value,
                    "capabilities": [
                        {
                            "name": cap.name,
                            "description": cap.description,
                            "tags": cap.tags
                        }
                        for cap in agent.capabilities
                    ],
                    "status": agent.status.value,
                    "endpoint": agent.endpoint,
                    "metadata": agent.metadata
                }
                for agent in agents
            ]
        
        @self.agent.tool
        async def get_agents_by_capability(
            ctx: RunContext[OrchestratorContext], 
            capability: str
        ) -> List[Dict[str, Any]]:
            """Get agents that have a specific capability"""
            agents = await ctx.deps.discovery_service.get_agents_by_capability(capability)
            
            return [
                {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "protocol": agent.protocol.value,
                    "capabilities": [cap.name for cap in agent.capabilities],
                    "status": agent.status.value
                }
                for agent in agents
            ]
        
        @self.agent.tool
        async def get_agents_by_protocol(
            ctx: RunContext[OrchestratorContext],
            protocol: str
        ) -> List[Dict[str, Any]]:
            """Get agents using a specific protocol"""
            try:
                protocol_type = ProtocolType(protocol.lower())
                agents = await ctx.deps.discovery_service.get_agents_by_protocol(protocol_type)
                
                return [
                    {
                        "agent_id": agent.agent_id,
                        "name": agent.name,
                        "capabilities": [cap.name for cap in agent.capabilities],
                        "status": agent.status.value
                    }
                    for agent in agents
                ]
            except ValueError:
                return []
    
    async def route_request(self, request: RoutingRequest) -> RoutingDecision:
        """Route a user request to the most appropriate agent"""
        start_time = datetime.utcnow()
        
        try:
            # Create context for the AI agent
            context = OrchestratorContext(
                discovery_service=self.discovery_service,
                request=request
            )
            
            # Prepare the query for the AI agent
            query = f"""
User Query: "{request.query}"
Context: {request.context or 'None'}
Required Capabilities: {request.required_capabilities or 'None'}
Preferred Protocol: {request.preferred_protocol or 'Any'}

Please analyze this query and determine the best agent to handle it. Consider:
1. What capabilities are needed to answer this query?
2. Which available agents have those capabilities?
3. What is the best match based on agent specialization?
4. How confident are you in this routing decision?

Return a routing decision with the selected agent ID, confidence score, and reasoning.
            """.strip()
            
            # Run the AI agent
            result = await self.agent.run(query, deps=context)
            
            # Extract the routing decision
            routing_decision = result.data
            
            # Update metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.total_requests += 1
            self.metrics.total_duration += duration
            
            if routing_decision.selected_agent_id:
                self.metrics.successful_routings += 1
            
            # Mark the selected agent as used
            if routing_decision.selected_agent_id:
                await self.discovery_service.mark_agent_request(routing_decision.selected_agent_id)
            
            logger.info(
                "Request routed successfully",
                query=request.query[:100] + "..." if len(request.query) > 100 else request.query,
                selected_agent=routing_decision.selected_agent_id,
                confidence=routing_decision.confidence,
                duration=duration
            )
            
            return routing_decision
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.total_requests += 1
            self.metrics.total_duration += duration
            self.metrics.failed_routings += 1
            
            logger.error(
                "Request routing failed",
                query=request.query[:100] + "..." if len(request.query) > 100 else request.query,
                error=str(e),
                duration=duration
            )
            
            # Return a fallback decision
            return RoutingDecision(
                selected_agent_id=None,
                confidence=0.0,
                reasoning=f"Routing failed due to error: {str(e)}",
                alternative_agents=[],
                estimated_response_time=30.0,
                requires_aggregation=False
            )
    
    async def process_request(self, request: RoutingRequest) -> AgentResponse:
        """Process a complete request: route and execute"""
        start_time = datetime.utcnow()
        
        try:
            # First, route the request
            routing_decision = await self.route_request(request)
            
            if not routing_decision.selected_agent_id:
                return AgentResponse(
                    success=False,
                    data=None,
                    error="No suitable agent found for this request",
                    duration=(datetime.utcnow() - start_time).total_seconds(),
                    agent_id=None,
                    metadata={
                        "routing_decision": routing_decision.dict(),
                        "reason": "no_agent_selected"
                    }
                )
            
            # Get the selected agent details
            agents = await self.discovery_service.get_healthy_agents()
            selected_agent = next(
                (agent for agent in agents if agent.agent_id == routing_decision.selected_agent_id),
                None
            )
            
            if not selected_agent:
                return AgentResponse(
                    success=False,
                    data=None,
                    error=f"Selected agent {routing_decision.selected_agent_id} is not available",
                    duration=(datetime.utcnow() - start_time).total_seconds(),
                    agent_id=routing_decision.selected_agent_id,
                    metadata={
                        "routing_decision": routing_decision.dict(),
                        "reason": "agent_not_available"
                    }
                )
            
            # Execute the request on the selected agent
            # This is a placeholder - actual implementation would depend on the protocol
            response_data = await self._execute_on_agent(selected_agent, request)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return AgentResponse(
                success=True,
                data=response_data,
                error=None,
                duration=duration,
                agent_id=selected_agent.agent_id,
                metadata={
                    "routing_decision": routing_decision.dict(),
                    "agent_protocol": selected_agent.protocol.value,
                    "agent_capabilities": [cap.name for cap in selected_agent.capabilities]
                }
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            logger.error(
                "Request processing failed",
                query=request.query,
                error=str(e),
                duration=duration
            )
            
            return AgentResponse(
                success=False,
                data=None,
                error=f"Request processing failed: {str(e)}",
                duration=duration,
                agent_id=None,
                metadata={"reason": "processing_error"}
            )
    
    async def _execute_on_agent(
        self, 
        agent: DiscoveredAgent, 
        request: RoutingRequest
    ) -> Dict[str, Any]:
        """Execute request on the selected agent (protocol-specific implementation)"""
        
        # This is a placeholder implementation
        # In a real implementation, this would:
        # 1. Use the appropriate protocol client (ACP, A2A, MCP)
        # 2. Format the request according to the protocol
        # 3. Send the request to the agent's endpoint
        # 4. Parse and return the response
        
        logger.info(
            "Executing request on agent",
            agent_id=agent.agent_id,
            protocol=agent.protocol.value,
            endpoint=agent.endpoint
        )
        
        # Simulate agent processing
        await asyncio.sleep(0.1)
        
        return {
            "message": f"Response from {agent.name}",
            "query": request.query,
            "agent_id": agent.agent_id,
            "protocol": agent.protocol.value,
            "timestamp": datetime.utcnow().isoformat(),
            "simulated": True  # Indicates this is a placeholder response
        }
    
    def get_metrics(self) -> OrchestrationMetrics:
        """Get current orchestration metrics"""
        return self.metrics
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the orchestrator agent"""
        discovery_healthy = await self.discovery_service.is_healthy()
        agent_count = len(await self.discovery_service.get_healthy_agents())
        
        return {
            "orchestrator_healthy": True,
            "discovery_service_healthy": discovery_healthy,
            "available_agents": agent_count,
            "llm_provider": self.settings.llm_provider.value,
            "model": str(type(self.model).__name__),
            "metrics": self.metrics.dict()
        }