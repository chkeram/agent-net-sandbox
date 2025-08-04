"""Unified discovery service that orchestrates protocol-specific strategies"""

import asyncio
import docker
import structlog
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from .models import (
    DiscoveredAgent, 
    AgentRegistryEntry, 
    AgentRegistry, 
    AgentStatus,
    ProtocolType
)
from .protocols import get_discovery_strategy
from .config import get_settings

logger = structlog.get_logger()


class UnifiedDiscoveryService:
    """Unified discovery service that orchestrates protocol-specific strategies"""
    
    def __init__(self):
        self.settings = get_settings()
        self.docker_client = None
        self.agent_registry: AgentRegistry = {}
        self._discovery_task: Optional[asyncio.Task] = None
        self._running = False
        
    async def start(self):
        """Start the discovery service"""
        logger.info("Starting unified discovery service")
        
        # Initialize Docker client if available
        if self.settings.docker_available:
            try:
                self.docker_client = docker.from_env()
                logger.info("Docker client initialized successfully")
            except Exception as e:
                logger.warning("Failed to initialize Docker client", error=str(e))
                self.docker_client = None
        else:
            logger.warning("Docker socket not available, discovery will be limited")
        
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
        
        if self.docker_client:
            try:
                self.docker_client.close()
            except Exception as e:
                logger.debug("Error closing Docker client", error=str(e))
        
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
        
        if not self.docker_client:
            logger.warning("Docker client not available, skipping discovery")
            return
        
        try:
            # Get all containers in the agent network
            containers = self._get_agent_containers()
            
            # Discover agents from containers
            discovered_agents = await self._discover_agents_from_containers(containers)
            
            # Update registry with health checks
            await self._update_registry(discovered_agents)
            
            # Clean up old/failed agents
            self._cleanup_registry()
            
            logger.info(
                "Discovery refresh complete",
                agents_found=len(self.agent_registry),
                healthy_agents=len(await self.get_healthy_agents())
            )
            
        except Exception as e:
            logger.error("Discovery refresh failed", error=str(e))
    
    def _get_agent_containers(self) -> List:
        """Get all containers that might be agents"""
        try:
            # Get containers from the agent network
            containers = self.docker_client.containers.list(
                filters={"network": self.settings.docker_network}
            )
            
            # Filter for containers with agent labels
            agent_containers = []
            for container in containers:
                try:
                    labels = container.attrs.get("Config", {}).get("Labels", {})
                    if any(label.startswith("agent.") for label in labels.keys()):
                        agent_containers.append(container)
                except Exception as e:
                    logger.debug(
                        "Error checking container labels",
                        container_id=container.id[:12],
                        error=str(e)
                    )
            
            logger.debug(
                "Found agent containers",
                total_containers=len(containers),
                agent_containers=len(agent_containers)
            )
            
            return agent_containers
            
        except Exception as e:
            logger.error("Failed to get agent containers", error=str(e))
            return []
    
    async def _discover_agents_from_containers(self, containers: List) -> List[DiscoveredAgent]:
        """Discover agents from a list of containers"""
        discovered_agents = []
        
        # Process containers concurrently
        tasks = []
        for container in containers:
            task = asyncio.create_task(self._discover_container(container))
            tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.debug("Container discovery failed", error=str(result))
                elif result is not None:
                    discovered_agents.append(result)
        
        return discovered_agents
    
    async def _discover_container(self, container) -> Optional[DiscoveredAgent]:
        """Discover agent from a single container"""
        try:
            # Get container info
            container_info = container.attrs
            
            # Extract protocol from labels
            labels = container_info.get("Config", {}).get("Labels", {})
            protocol_str = labels.get("agent.protocol", "").lower()
            
            # Skip non-agent containers and the orchestrator itself
            if not protocol_str or protocol_str == "orchestrator":
                return None
            
            # Get appropriate discovery strategy
            strategy = get_discovery_strategy(protocol_str)
            
            # Discover the agent using the strategy
            agent = await strategy.discover(container_info)
            
            if agent:
                logger.debug(
                    "Agent discovered",
                    agent_id=agent.agent_id,
                    protocol=agent.protocol,
                    capabilities=len(agent.capabilities)
                )
            
            return agent
            
        except Exception as e:
            container_id = getattr(container, 'id', 'unknown')[:12]
            logger.debug(
                "Failed to discover container",
                container_id=container_id,
                error=str(e)
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