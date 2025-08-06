#!/usr/bin/env python3
"""
Docker entrypoint for A2A Math Agent - fixes asyncio event loop issues
"""

import os
from a2a_math_agent import MathAgent, create_agent_card
from a2a.server.apps.jsonrpc.fastapi_app import A2AFastAPIApplication
from a2a.server.request_handlers.default_request_handler import DefaultRequestHandler
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.server.events.in_memory_queue_manager import InMemoryQueueManager
import uvicorn


def main():
    """Main entry point for the A2A Math Agent."""
    
    print("🧮 Starting A2A Math Agent (Docker)")
    
    # Create agent card
    agent_card = create_agent_card()
    print(f"Agent: {agent_card.name}")
    print(f"Description: {agent_card.description}")
    print(f"Skills: {[skill.name for skill in agent_card.skills]}")
    
    # Create math agent executor
    math_agent = MathAgent()
    
    # Create required dependencies
    task_store = InMemoryTaskStore()
    queue_manager = InMemoryQueueManager()
    
    # Create request handler with the agent executor
    request_handler = DefaultRequestHandler(
        agent_executor=math_agent,
        task_store=task_store,
        queue_manager=queue_manager
    )
    
    # Create A2A FastAPI application
    a2a_app = A2AFastAPIApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )
    
    # Build the FastAPI app instance
    fastapi_app = a2a_app.build()
    
    # Get port from environment
    port = int(os.getenv("A2A_PORT", "8002"))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"🚀 Starting server on http://{host}:{port}")
    print(f"📡 Agent card available at: http://localhost:{port}/.well-known/agent-card.json")
    
    # Run the server (this doesn't create a conflicting event loop)
    uvicorn.run(fastapi_app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()