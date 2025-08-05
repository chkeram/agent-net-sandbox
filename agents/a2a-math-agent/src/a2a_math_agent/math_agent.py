#!/usr/bin/env python3
"""
A2A Math Operations Agent
A mathematical computation agent using the A2A Protocol SDK
"""

import asyncio
import math
import re
import os
import logging
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from a2a.server.apps.jsonrpc.fastapi_app import A2AFastAPIApplication
from a2a.types import (
    AgentCard, 
    AgentSkill, 
    AgentCapabilities,
    Message, 
    TextPart, 
    Task
)
from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.request_handlers.default_request_handler import DefaultRequestHandler
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.server.events.in_memory_queue_manager import InMemoryQueueManager

# Import LLM service
from .llm_service import LLMService

# Simple mathematical operations (not using LangChain for now)
class MathOperations:
    """Simple mathematical operations."""
    
    @staticmethod
    def add(a: float, b: float) -> float:
        """Add two numbers."""
        return a + b
    
    @staticmethod
    def subtract(a: float, b: float) -> float:
        """Subtract second number from first."""
        return a - b
    
    @staticmethod
    def multiply(a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b
    
    @staticmethod
    def divide(a: float, b: float) -> float:
        """Divide first number by second."""
        if b == 0:
            raise ValueError("Division by zero is not allowed")
        return a / b
    
    @staticmethod
    def sqrt(number: float) -> float:
        """Calculate square root."""
        if number < 0:
            raise ValueError("Cannot calculate square root of negative number")
        return math.sqrt(number)
    
    @staticmethod
    def power(base: float, exponent: float) -> float:
        """Raise base to the power of exponent."""
        return math.pow(base, exponent)


class MathAgent(AgentExecutor):
    """A2A Mathematical Operations Agent with LLM support."""
    
    def __init__(self):
        super().__init__()
        self.math_ops = MathOperations()
        self.llm_service = LLMService()
        self.logger = logging.getLogger(__name__)
    
    async def cancel(self, context: RequestContext) -> None:
        """Cancel the current operation (not applicable for math operations)."""
        pass
    
    async def execute(self, context: RequestContext) -> None:
        """Execute mathematical operations based on A2A message."""
        try:
            # Get the message from context
            message = context.request.message
            
            # Process the message content
            result = await self._process_message(message)
            
            # Create response message
            response_parts = [TextPart(text=str(result))]
            response_message = Message(
                message_id="agent_response",
                role="agent",
                parts=response_parts
            )
            
            # Send response
            await context.send_message(response_message)
            
        except Exception as e:
            # Send error response
            error_parts = [TextPart(text=f"Error: {str(e)}")]
            error_message = Message(
                message_id="agent_error",
                role="agent",
                parts=error_parts
            )
            await context.send_message(error_message)
    
    async def _process_message(self, message: Message) -> str:
        """Process incoming message and perform mathematical operations."""
        # Extract text from message parts
        text_content = ""
        for part in message.parts:
            # Parts are wrapped in Part objects with a root attribute
            if hasattr(part, 'root') and isinstance(part.root, TextPart):
                text_content += part.root.text + " "
            elif isinstance(part, TextPart):
                text_content += part.text + " "
        
        text_content = text_content.strip()
        
        # Log LLM availability status
        self.logger.info(f"LLM available: {self.llm_service.is_llm_available()}")
        if self.llm_service.is_llm_available():
            self.logger.info(f"LLM status: {self.llm_service.get_provider_status()}")
        
        # Try LLM first if available
        if self.llm_service.is_llm_available():
            try:
                self.logger.info(f"Attempting LLM processing for: {text_content}")
                llm_response = await self.llm_service.generate_response(text_content)
                return f"🤖 LLM: {llm_response}"
            except Exception as e:
                self.logger.warning(f"LLM processing failed: {e}, falling back to deterministic calculation")
        
        # Fallback to deterministic calculation
        self.logger.info("Using deterministic calculation")
        return f"🧮 Calc: {self._evaluate_expression(text_content.lower())}"
    
    def _evaluate_expression(self, expression: str) -> str:
        """Evaluate mathematical expressions using pattern matching."""
        expression = expression.strip()
        
        # Remove common question words and extra phrases (case insensitive)
        expression = re.sub(r'^(what is|calculate|compute|find|solve)\s+', '', expression, flags=re.IGNORECASE)
        expression = re.sub(r'\s+(please|for me|\?)$', '', expression, flags=re.IGNORECASE)
        expression = re.sub(r'\?$', '', expression)
        
        try:
            # Addition pattern
            if '+' in expression:
                parts = expression.split('+')
                if len(parts) == 2:
                    a = float(parts[0].strip())
                    b = float(parts[1].strip())
                    result = self.math_ops.add(a, b)
                    return f"{a} + {b} = {result}"
            
            # Subtraction pattern (but not inside function calls)
            elif '-' in expression and not expression.startswith('-') and 'sqrt(' not in expression:
                parts = expression.split('-')
                if len(parts) == 2:
                    a = float(parts[0].strip())
                    b = float(parts[1].strip())
                    result = self.math_ops.subtract(a, b)
                    return f"{a} - {b} = {result}"
            
            # Power pattern (check before multiplication to avoid ** being split on *)
            elif '**' in expression or '^' in expression:
                separator = '**' if '**' in expression else '^'
                parts = expression.split(separator)
                if len(parts) == 2:
                    try:
                        base = float(parts[0].strip())
                        exponent = float(parts[1].strip())
                        result = self.math_ops.power(base, exponent)
                        return f"{base}^{exponent} = {result}"
                    except ValueError:
                        # Not a valid numeric power expression, continue to fallback
                        pass
            
            # Multiplication pattern
            elif '*' in expression or '×' in expression:
                separator = '*' if '*' in expression else '×'
                parts = expression.split(separator)
                if len(parts) == 2:
                    a = float(parts[0].strip())
                    b = float(parts[1].strip())
                    result = self.math_ops.multiply(a, b)
                    return f"{a} {separator} {b} = {result}"
            
            # Division pattern
            elif '/' in expression or '÷' in expression:
                separator = '/' if '/' in expression else '÷'
                parts = expression.split(separator)
                if len(parts) == 2:
                    a = float(parts[0].strip())
                    b = float(parts[1].strip())
                    result = self.math_ops.divide(a, b)
                    return f"{a} {separator} {b} = {result}"
            
            # Square root pattern
            elif 'sqrt' in expression:
                match = re.search(r'sqrt\s*\(\s*(-?[0-9.]+)\s*\)', expression)
                if match:
                    number = float(match.group(1))
                    result = self.math_ops.sqrt(number)
                    return f"√{number} = {result}"
            
            # Try to evaluate as a simple number
            try:
                number = float(expression)
                return f"The number is: {number}"
            except ValueError:
                pass
            
            return f"I can help with basic math operations like: 5 + 3, 10 - 4, 6 * 7, 15 / 3, sqrt(16), 2^3. Please try one of these formats."
            
        except ValueError as e:
            error_msg = str(e)
            # Return sqrt errors directly without prefix
            if "Cannot calculate square root" in error_msg or "Division by zero" in error_msg:
                return error_msg
            return f"Invalid number format: {error_msg}"
        except Exception as e:
            return f"Calculation error: {str(e)}"


def create_agent_card() -> AgentCard:
    """Create the agent card describing this math agent's capabilities."""
    
    # Check LLM availability to adjust capabilities
    llm_service = LLMService()
    llm_available = llm_service.is_llm_available()
    provider_status = llm_service.get_provider_status()
    
    # Define mathematical skills
    skills = [
        AgentSkill(
            id="basic_arithmetic",
            name="Basic Arithmetic",
            description="Perform basic arithmetic operations: addition, subtraction, multiplication, division",
            examples=["5 + 3", "10 - 4", "6 * 7", "15 / 3"],
            tags=["arithmetic", "math", "basic", "deterministic"]
        ),
        AgentSkill(
            id="advanced_math",
            name="Advanced Mathematics", 
            description="Perform advanced mathematical operations like square roots and exponentiation",
            examples=["sqrt(16)", "2^3", "5**2"],
            tags=["advanced", "math", "power", "roots", "deterministic"]
        )
    ]
    
    # Add LLM-powered skill if available
    if llm_available:
        available_providers = provider_status.get("available_providers", [])
        skills.append(
            AgentSkill(
                id="llm_math",
                name="LLM-Powered Mathematics",
                description=f"Natural language mathematical problem solving using AI ({', '.join(available_providers)})",
                examples=[
                    "What is the derivative of x^2?",
                    "Solve 2x + 5 = 13",
                    "Calculate the area of a circle with radius 5",
                    "Convert 32 Fahrenheit to Celsius"
                ],
                tags=["llm", "natural-language", "ai", "complex-math"] + available_providers
            )
        )
    
    # Create description based on capabilities
    base_description = "A mathematical computation agent using the A2A protocol"
    if llm_available:
        available_providers = provider_status.get("available_providers", [])
        description = f"{base_description} with AI-powered problem solving ({', '.join(available_providers)}) and deterministic calculation fallback"
    else:
        description = f"{base_description} with deterministic mathematical calculations"
    
    return AgentCard(
        name="A2A Math Operations Agent",
        description=description,
        version="0.1.0",
        skills=skills,
        capabilities=AgentCapabilities(),
        default_input_modes=["text"],
        default_output_modes=["text"],
        url="http://localhost:8002"
    )


async def main():
    """Main entry point for the A2A Math Agent."""
    
    # Create agent card
    agent_card = create_agent_card()
    
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
    
    # Run the server
    import uvicorn
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8002)


if __name__ == "__main__":
    asyncio.run(main())