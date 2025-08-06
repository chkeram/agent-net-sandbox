#!/usr/bin/env python3
"""
Test script to start the A2A Math Agent server
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from a2a_math_agent import MathAgent, create_agent_card
from a2a.server.apps.jsonrpc.fastapi_app import A2AFastAPIApplication
from a2a.server.request_handlers.default_request_handler import DefaultRequestHandler
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.server.events.in_memory_queue_manager import InMemoryQueueManager
import uvicorn


def main():
    """Main entry point for the A2A Math Agent."""
    
    # Clear LLM environment variables for testing without LLM
    os.environ.pop('OPENAI_API_KEY', None)
    os.environ.pop('ANTHROPIC_API_KEY', None) 
    os.environ.pop('GEMINI_API_KEY', None)
    os.environ['LLM_PROVIDER'] = 'none'
    
    print("🧮 Starting A2A Math Agent (No LLM mode)")
    
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
    
    print("🚀 Starting server on http://0.0.0.0:8002")
    print("📡 Agent card available at: http://localhost:8002/.well-known/agent-card")
    print("🔗 Send messages to: http://localhost:8002/send-message")
    
    # Run the server
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8002, log_level="info")


if __name__ == "__main__":
    main()