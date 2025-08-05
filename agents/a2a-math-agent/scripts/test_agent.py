#!/usr/bin/env python3
"""
Test script for the A2A Math Agent
"""

import asyncio
import sys
import os

# Add src directory to Python path for script execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from a2a_math_agent import MathAgent, create_agent_card


async def test_agent():
    """Test the math agent functionality."""
    
    print("=== A2A Math Agent Test ===")
    
    # Test agent card creation
    agent_card = create_agent_card()
    print(f"Agent Name: {agent_card.name}")
    print(f"Description: {agent_card.description}")
    print(f"Version: {agent_card.version}")
    print(f"Skills: {[skill.name for skill in agent_card.skills]}")
    print()
    
    # Test math operations
    agent = MathAgent()
    
    # Test expression evaluation
    test_expressions = [
        "5 + 3",
        "10 - 4", 
        "6 * 7",
        "15 / 3",
        "sqrt(16)",
        "2^3",
        "what is 25 + 17?",
        "calculate 100 / 5"
    ]
    
    print("=== Math Expression Tests ===")
    for expr in test_expressions:
        try:
            result = agent._evaluate_expression(expr)
            print(f"'{expr}' → {result}")
        except Exception as e:
            print(f"'{expr}' → Error: {e}")
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_agent())