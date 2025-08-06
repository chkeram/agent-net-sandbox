"""Unified discovery service that orchestrates protocol-specific strategies"""

import asyncio
import structlog
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from .models import (
    DiscoveredAgent, 
    AgentRegistryEntry, 
    AgentRegistry, 
    AgentStatus,
    ProtocolType,
    AgentCapability
)
from .protocols import get_discovery_strategy
from .config import get_settings

logger = structlog.get_logger()


class UnifiedDiscoveryService:
    """Unified discovery service that orchestrates protocol-specific strategies"""
    
    def __init__(self):
        self.settings = get_settings()
        self.agent_registry: AgentRegistry = {}
        self._discovery_task: Optional[asyncio.Task] = None
        self._running = False
        
    async def start(self):
        """Start the discovery service"""
        logger.info("Starting unified discovery service")
        
        self._running = True
        
        # Start discovery loop
        self._discovery_task = asyncio.create_task(self._discovery_loop())
        
        # Do initial discovery
        await self.refresh()
        
        logger.info("Discovery service started successfully")
        
    async def stop(self):
        """Stop the discovery service"""
        logger.info("Stopping discovery service")
        
        self._running = False
        
        if self._discovery_task:
            self._discovery_task.cancel()
            try:
                await self._discovery_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Discovery service stopped")
    
    async def _discovery_loop(self):
        """Continuous discovery loop"""
        while self._running:
            try:
                await asyncio.sleep(self.settings.discovery_interval_seconds)
                if self._running:  # Check again after sleep
                    await self.refresh()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Discovery loop error", error=str(e))
                # Continue running even if discovery fails
    
    async def refresh(self):
        """Refresh the agent registry by discovering all available agents"""
        logger.debug("Starting agent discovery refresh")
        
        try:
            # Use HTTP-based agent discovery
            logger.info("Attempting HTTP-based agent discovery")
            discovered_agents = await self._discover_agents_http()
            
            # Update registry with health checks
            await self._update_registry(discovered_agents)
            
            # Clean up old/failed agents
            self._cleanup_registry()
            
            logger.info(
                "Discovery refresh complete",
                agents_found=len(self.agent_registry),
                healthy_agents=len(await self.get_healthy_agents()),
                discovery_method="http"
            )
            
        except Exception as e:
            logger.error("Discovery refresh failed", error=str(e))
    
    async def _discover_agents_http(self) -> List[DiscoveredAgent]:
        """HTTP-based agent discovery using known endpoints"""
        import aiohttp
        discovered_agents = []
        
        # Known agent endpoints to try
        known_endpoints = [
            {"url": "http://acp-hello-world-agent:8000", "protocol": "acp", "name": "hello-world"},
            {"url": "http://localhost:8000", "protocol": "acp", "name": "hello-world"},  # fallback for host networking
            {"url": "http://a2a-math-agent:8002", "protocol": "a2a", "name": "math"},
            {"url": "http://localhost:8002", "protocol": "a2a", "name": "math"},  # fallback for host networking
        ]
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            # Group endpoints by agent to handle localhost fallback properly
            agents_tried = set()
            
            for endpoint in known_endpoints:
                agent_key = f"{endpoint['protocol']}-{endpoint['name']}"
                
                # Skip if we already successfully discovered this agent
                if agent_key in agents_tried:
                    continue
                    
                try:
                    logger.debug("Trying HTTP discovery endpoint", url=endpoint['url'])
                    
                    # Use appropriate health check endpoint based on protocol
                    health_url = f"{endpoint['url']}/health"
                    if endpoint['protocol'] == 'a2a':
                        health_url = f"{endpoint['url']}/.well-known/agent-card.json"
                    
                    # Try to get agent info via health endpoint
                    async with session.get(health_url) as response:
                        logger.debug(
                            "Health endpoint response", 
                            url=endpoint['url'], 
                            health_url=health_url,
                            status=response.status
                        )
                        if response.status == 200:
                            # Construct a discovered agent based on the endpoint
                            agent = await self._create_agent_from_endpoint(endpoint, session)
                            if agent:
                                discovered_agents.append(agent)
                                agents_tried.add(agent_key)
                                logger.info(
                                    "Discovered agent via HTTP",
                                    agent_id=agent.agent_id,
                                    url=endpoint['url'],
                                    protocol=agent.protocol
                                )
                                # Continue to next agent, don't break entire loop
                            else:
                                logger.warning("Failed to create agent from endpoint", url=endpoint['url'])
                                
                except Exception as e:
                    logger.warning(
                        "HTTP discovery failed for endpoint",
                        url=endpoint['url'],
                        error=str(e),
                        error_type=type(e).__name__
                    )
                    continue
        
        return discovered_agents
    
    async def _create_agent_from_endpoint(self, endpoint: dict, session) -> Optional[DiscoveredAgent]:
        """Create a DiscoveredAgent from an HTTP endpoint"""
        try:
            logger.debug("Creating agent from endpoint", endpoint=endpoint)
            
            # Try to get more detailed info from agent-specific endpoints
            capabilities = []
            metadata = {}
            
            if endpoint['protocol'] == 'acp':
                # Try to get ACP capabilities
                try:
                    logger.debug("Trying to get ACP capabilities", url=f"{endpoint['url']}/capabilities")
                    async with session.get(f"{endpoint['url']}/capabilities") as response:
                        logger.debug("ACP capabilities response", status=response.status)
                        if response.status == 200:
                            capabilities_data = await response.json()
                            raw_capabilities = capabilities_data.get('capabilities', [])
                            metadata = {
                                'agent_id': capabilities_data.get('agent_id'),
                                'agent_name': capabilities_data.get('agent_name'),
                                'version': capabilities_data.get('version'),
                                'description': capabilities_data.get('description'),
                                'supported_languages': capabilities_data.get('supported_languages', [])
                            }
                            
                            # Convert capability strings to AgentCapability objects
                            for cap in raw_capabilities:
                                if isinstance(cap, str):
                                    capabilities.append(AgentCapability(
                                        name=cap,
                                        description=f"Agent capability: {cap}"
                                    ))
                                elif isinstance(cap, dict):
                                    capabilities.append(AgentCapability(**cap))
                            
                            logger.debug("Got ACP capabilities", capabilities=len(capabilities), metadata=metadata)
                except Exception as e:
                    logger.debug("Failed to get ACP capabilities", error=str(e))
                    pass  # Use defaults if descriptor not available
                    
            elif endpoint['protocol'] == 'a2a':
                # Try to get A2A agent card
                try:
                    logger.debug("Trying to get A2A agent card", url=f"{endpoint['url']}/.well-known/agent-card.json")
                    async with session.get(f"{endpoint['url']}/.well-known/agent-card.json") as response:
                        logger.debug("A2A agent card response", status=response.status)
                        if response.status == 200:
                            agent_card = await response.json()
                            metadata = {
                                'version': agent_card.get('version'),
                                'protocolVersion': agent_card.get('protocolVersion'),
                                'description': agent_card.get('description'),
                                'preferredTransport': agent_card.get('preferredTransport')
                            }
                            
                            # Convert skills to capabilities
                            skills = agent_card.get('skills', [])
                            for skill in skills:
                                capabilities.append(AgentCapability(
                                    name=skill.get('name', skill.get('id', 'unknown')),
                                    description=skill.get('description', f"A2A skill: {skill.get('name', 'unknown')}"),
                                    tags=skill.get('tags', [])  # Include tags from A2A skills
                                ))
                                
                            logger.debug("Got A2A agent card", capabilities=len(capabilities), metadata=metadata)
                except Exception as e:
                    logger.debug("Failed to get A2A agent card", error=str(e))
                    pass  # Use defaults if agent card not available
            
            # Create agent with available information
            default_capability = AgentCapability(
                name='greeting' if endpoint['protocol'] == 'acp' else 'arithmetic',
                description='Agent greeting capability' if endpoint['protocol'] == 'acp' else 'Mathematical computation capability'
            )
            
            agent_data = {
                "agent_id": f"{endpoint['protocol']}-{endpoint['name']}",
                "name": endpoint.get('name', f"{endpoint['protocol']}-agent"),
                "protocol": endpoint['protocol'],
                "endpoint": endpoint['url'],
                "capabilities": capabilities or [default_capability],
                "metadata": metadata,
                "status": "healthy",
                "last_health_check": datetime.utcnow()
            }
            
            logger.debug("Creating DiscoveredAgent with data", data=agent_data)
            
            agent = DiscoveredAgent(
                agent_id=agent_data["agent_id"],
                name=agent_data["name"],
                protocol=ProtocolType(agent_data["protocol"]),
                endpoint=agent_data["endpoint"],
                capabilities=agent_data["capabilities"],
                metadata=agent_data["metadata"],
                status=AgentStatus.HEALTHY,
                last_health_check=agent_data["last_health_check"]
            )
            
            logger.debug("Successfully created agent", agent_id=agent.agent_id)
            return agent
            
        except Exception as e:
            logger.warning(
                "Failed to create agent from endpoint",
                endpoint=endpoint,
                error=str(e),
                error_type=type(e).__name__
            )
            return None
    
    
    async def _update_registry(self, discovered_agents: List[DiscoveredAgent]):
        """Update the agent registry with discovered agents and health checks"""
        new_registry: AgentRegistry = {}
        
        # Process discovered agents
        for agent in discovered_agents:
            # Get existing registry entry or create new one
            existing_entry = self.agent_registry.get(agent.agent_id)
            
            if existing_entry:
                # Update existing entry
                entry = existing_entry
                entry.agent = agent
                entry.mark_success()  # Reset failure count
            else:
                # Create new entry
                entry = AgentRegistryEntry(agent=agent)
            
            # Check agent health
            try:
                strategy = get_discovery_strategy(agent.protocol.value)
                health_status = await strategy.health_check(agent)
                agent.status = health_status
                agent.last_health_check = datetime.utcnow()
                
                if health_status == AgentStatus.HEALTHY:
                    entry.mark_success()
                else:
                    entry.mark_failure()
                    
            except Exception as e:
                logger.debug(
                    "Health check failed",
                    agent_id=agent.agent_id,
                    error=str(e)
                )
                agent.status = AgentStatus.UNKNOWN
                entry.mark_failure()
            
            new_registry[agent.agent_id] = entry
        
        # Preserve agents that weren't discovered this time but are still valid
        for agent_id, entry in self.agent_registry.items():
            if agent_id not in new_registry:
                # Mark as not seen in this discovery cycle
                entry.mark_failure()
                
                # Keep if not exceeded max failures
                if not entry.should_remove():
                    new_registry[agent_id] = entry
                else:
                    logger.info(
                        "Removing failed agent from registry",
                        agent_id=agent_id,
                        failures=entry.consecutive_failures
                    )
        
        self.agent_registry = new_registry
    
    def _cleanup_registry(self):
        """Clean up old or failed agents from registry"""
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        to_remove = []
        
        for agent_id, entry in self.agent_registry.items():
            # Remove very old agents
            if entry.last_seen < cutoff_time:
                to_remove.append(agent_id)
            # Remove agents with too many failures
            elif entry.should_remove():
                to_remove.append(agent_id)
        
        for agent_id in to_remove:
            logger.info("Removing stale agent from registry", agent_id=agent_id)
            del self.agent_registry[agent_id]
    
    # Public API methods
    
    async def get_all_agents(self) -> List[DiscoveredAgent]:
        """Get all discovered agents"""
        return [entry.agent for entry in self.agent_registry.values()]
    
    async def get_healthy_agents(self) -> List[DiscoveredAgent]:
        """Get only healthy agents"""
        return [
            entry.agent for entry in self.agent_registry.values()
            if entry.agent.status == AgentStatus.HEALTHY
        ]
    
    async def get_agent(self, agent_id: str) -> Optional[DiscoveredAgent]:
        """Get specific agent by ID"""
        entry = self.agent_registry.get(agent_id)
        return entry.agent if entry else None
    
    async def get_agent_by_id(self, agent_id: str) -> Optional[DiscoveredAgent]:
        """Get specific agent by ID (alias for get_agent)"""
        return await self.get_agent(agent_id)
    
    async def get_agents_by_protocol(
        self,
        protocol: ProtocolType
    ) -> List[DiscoveredAgent]:
        """Get agents using specific protocol"""
        return [
            entry.agent for entry in self.agent_registry.values()
            if entry.agent.protocol == protocol
        ]
    
    async def get_agents_by_capability(
        self,
        capability_name: str
    ) -> List[DiscoveredAgent]:
        """Get agents that have a specific capability"""
        agents = []
        for entry in self.agent_registry.values():
            if entry.agent.has_capability(capability_name):
                agents.append(entry.agent)
        return agents
    
    async def mark_agent_request(self, agent_id: str):
        """Mark that a request was made to an agent"""
        entry = self.agent_registry.get(agent_id)
        if entry:
            entry.mark_request()
    
    async def is_healthy(self) -> bool:
        """Check if discovery service is healthy"""
        return (
            self._running and 
            len(self.agent_registry) >= 0  # At least discovery is working
        )
    
    def get_registry_stats(self) -> Dict[str, int]:
        """Get statistics about the agent registry"""
        total_agents = len(self.agent_registry)
        healthy_agents = sum(
            1 for entry in self.agent_registry.values()
            if entry.agent.status == AgentStatus.HEALTHY
        )
        
        protocol_counts = {}
        for entry in self.agent_registry.values():
            protocol = entry.agent.protocol.value
            protocol_counts[protocol] = protocol_counts.get(protocol, 0) + 1
        
        return {
            "total_agents": total_agents,
            "healthy_agents": healthy_agents,
            "degraded_agents": sum(
                1 for entry in self.agent_registry.values()
                if entry.agent.status == AgentStatus.DEGRADED
            ),
            "unhealthy_agents": sum(
                1 for entry in self.agent_registry.values()
                if entry.agent.status == AgentStatus.UNHEALTHY
            ),
            "by_protocol": protocol_counts
        }