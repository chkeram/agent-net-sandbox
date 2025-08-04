"""Protocol client implementations for multi-protocol agent communication"""

from .base import ProtocolClient, DiscoveryStrategy
from .acp_discovery import ACPDiscoveryStrategy
from .a2a_discovery import A2ADiscoveryStrategy
from .mcp_discovery import MCPDiscoveryStrategy

__all__ = [
    "ProtocolClient",
    "DiscoveryStrategy", 
    "ACPDiscoveryStrategy",
    "A2ADiscoveryStrategy",
    "MCPDiscoveryStrategy",
]


def get_discovery_strategy(protocol: str) -> DiscoveryStrategy:
    """Get appropriate discovery strategy for protocol"""
    from ..models import ProtocolType
    
    strategy_map = {
        ProtocolType.ACP: ACPDiscoveryStrategy,
        ProtocolType.A2A: A2ADiscoveryStrategy,
        ProtocolType.MCP: MCPDiscoveryStrategy,
    }
    
    try:
        protocol_type = ProtocolType(protocol.lower())
        strategy_class = strategy_map.get(protocol_type)
        if strategy_class:
            return strategy_class()
    except ValueError:
        pass
    
    # Fallback to generic strategy
    from .base import GenericDiscoveryStrategy
    return GenericDiscoveryStrategy()