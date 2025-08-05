#!/usr/bin/env python3
"""
Test script for LLM integration in A2A Math Agent
"""

import asyncio
import os
import logging
import sys

# Add src directory to Python path for script execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from a2a_math_agent import MathAgent, create_agent_card, LLMService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


async def test_without_llm():
    """Test agent behavior without LLM configuration."""
    print("🧮 === Testing WITHOUT LLM Configuration ===")
    
    # Ensure no LLM environment variables are set
    llm_env_vars = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GEMINI_API_KEY', 'LLM_PROVIDER']
    for var in llm_env_vars:
        if var in os.environ:
            del os.environ[var]
    
    # Create fresh agent
    agent = MathAgent()
    
    print(f"LLM Available: {agent.llm_service.is_llm_available()}")
    print(f"Provider Status: {agent.llm_service.get_provider_status()}")
    
    # Test agent card
    agent_card = create_agent_card()
    print(f"Agent Description: {agent_card.description}")
    print(f"Skills Count: {len(agent_card.skills)}")
    print(f"Skills: {[skill.name for skill in agent_card.skills]}")
    
    # Test mathematical expressions
    test_cases = [
        "5 + 3",
        "What is 12 * 8?",
        "Calculate sqrt(25)",
        "Solve a complex integral"  # This should fall back to deterministic
    ]
    
    print("\n📊 Test Results:")
    for test_case in test_cases:
        # Simulate message processing
        if agent.llm_service.is_llm_available():
            try:
                result = await agent.llm_service.generate_response(test_case)
                result = f"🤖 LLM: {result}"
            except Exception:
                result = f"🧮 Calc: {agent._evaluate_expression(test_case.lower())}"
        else:
            result = f"🧮 Calc: {agent._evaluate_expression(test_case.lower())}"
        
        print(f"  '{test_case}' → {result}")
    
    print()


async def test_with_mock_llm():
    """Test agent behavior with mock LLM configuration."""
    print("🤖 === Testing WITH Mock LLM Configuration ===")
    
    # Set mock environment (without real API keys for testing)
    os.environ['LLM_PROVIDER'] = 'openai'
    os.environ['OPENAI_API_KEY'] = 'mock-key-for-testing'  # This will fail gracefully
    
    # Create fresh agent
    agent = MathAgent()
    
    print(f"LLM Available: {agent.llm_service.is_llm_available()}")
    print(f"Provider Status: {agent.llm_service.get_provider_status()}")
    
    # Test agent card with LLM
    agent_card = create_agent_card()
    print(f"Agent Description: {agent_card.description}")
    print(f"Skills Count: {len(agent_card.skills)}")
    print(f"Skills: {[skill.name for skill in agent_card.skills]}")
    
    # Test mathematical expressions (will fail and fallback)
    test_cases = [
        "What is 7 + 5?",
        "Calculate the derivative of x^2"
    ]
    
    print("\n📊 Test Results (Mock LLM - will fallback to deterministic):")
    for test_case in test_cases:
        # Simulate message processing with expected failure
        if agent.llm_service.is_llm_available():
            try:
                result = await agent.llm_service.generate_response(test_case)
                result = f"🤖 LLM: {result}"
            except Exception as e:
                print(f"  LLM failed as expected (mock key): {type(e).__name__}")
                result = f"🧮 Calc: {agent._evaluate_expression(test_case.lower())}"
        else:
            result = f"🧮 Calc: {agent._evaluate_expression(test_case.lower())}"
        
        print(f"  '{test_case}' → {result}")
    
    print()


async def test_server_creation():
    """Test that the enhanced agent can still create A2A servers."""
    print("🔧 === Testing A2A Server Creation ===")
    
    try:
        agent_card = create_agent_card()
        math_agent_executor = MathAgent()
        task_store = __import__('math_agent').InMemoryTaskStore()
        queue_manager = __import__('math_agent').InMemoryQueueManager()
        request_handler = __import__('math_agent').DefaultRequestHandler(
            agent_executor=math_agent_executor,
            task_store=task_store,
            queue_manager=queue_manager
        )
        a2a_app = __import__('math_agent').A2AFastAPIApplication(
            agent_card=agent_card,
            http_handler=request_handler
        )
        fastapi_app = a2a_app.build()
        
        print("✅ A2A Server creation successful!")
        print(f"FastAPI app type: {type(fastapi_app)}")
        print(f"Agent capabilities: {len(agent_card.skills)} skills")
        
    except Exception as e:
        print(f"❌ A2A Server creation failed: {e}")
        import traceback
        traceback.print_exc()


def show_llm_configuration_guide():
    """Show how to configure LLM providers."""
    print("📖 === LLM Configuration Guide ===")
    print()
    print("To enable LLM integration, set environment variables:")
    print()
    print("For OpenAI:")
    print("  export OPENAI_API_KEY='your-openai-api-key'")
    print("  export LLM_PROVIDER='openai'")
    print("  export OPENAI_MODEL='gpt-4o-mini'  # optional")
    print()
    print("For Anthropic:")
    print("  export ANTHROPIC_API_KEY='your-anthropic-api-key'")
    print("  export LLM_PROVIDER='anthropic'")
    print("  export ANTHROPIC_MODEL='claude-3-haiku-20240307'  # optional")
    print()
    print("For Gemini:")
    print("  export GEMINI_API_KEY='your-gemini-api-key'")
    print("  export LLM_PROVIDER='gemini'")
    print("  export GEMINI_MODEL='gemini-1.5-flash'  # optional")
    print()
    print("Or create a .env file with these variables.")
    print("See .env.example for a complete template.")
    print()


async def main():
    """Run all tests."""
    print("🧮🤖 A2A Math Agent - LLM Integration Test Suite")
    print("=" * 55)
    print()
    
    await test_without_llm()
    await test_with_mock_llm()
    await test_server_creation()
    show_llm_configuration_guide()
    
    print("✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())