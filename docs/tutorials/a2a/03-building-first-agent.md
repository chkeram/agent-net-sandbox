# Part 3: Building Your First A2A Agent

## 🎯 Learning Objectives

By the end of this tutorial, you will:
- Build a complete A2A agent from scratch using the A2A SDK
- Implement proper message handling and response generation
- Create skill-based processing and routing logic
- Add comprehensive error handling and validation
- Test and deploy your agent with orchestrator integration

## 📚 Prerequisites

- Completed [Part 1: Understanding A2A Fundamentals](./01-understanding-a2a.md)
- Completed [Part 2: Configuration & Discovery](./02-configuration-discovery.md)
- Python 3.11+ installed with virtual environment support
- Basic understanding of async Python and FastAPI
- Access to our existing A2A Math Agent for reference

## 🚀 Project Setup

Let's create a new A2A agent step by step. We'll build a "Text Processing Agent" that demonstrates core A2A patterns.

### **1. Create Project Structure**

```bash
# Create project directory
mkdir a2a-text-agent
cd a2a-text-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Create project structure
mkdir -p src/a2a_text_agent
mkdir -p tests
mkdir -p scripts
touch src/a2a_text_agent/__init__.py
touch README.md
touch requirements.txt
touch .env.example
touch .env
```

### **2. Install Dependencies**

```bash
# requirements.txt
cat > requirements.txt << 'EOF'
# A2A SDK and FastAPI
a2a-sdk>=0.3.0
fastapi>=0.100.0
uvicorn>=0.23.0

# Data processing
pydantic>=2.0.0
python-dotenv>=1.0.0

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.25.0

# Optional: Enhanced text processing
nltk>=3.8.0
textstat>=0.7.0
EOF

# Install dependencies
pip install -r requirements.txt
```

### **3. Environment Configuration**

```bash
# .env.example
cat > .env.example << 'EOF'
# Server Configuration
A2A_PORT=8003
HOST=0.0.0.0

# Agent Configuration
AGENT_NAME="A2A Text Processing Agent"
AGENT_VERSION=0.1.0
AGENT_DESCRIPTION="Text analysis and processing agent using A2A protocol"

# Text Processing Features
ENABLE_SENTIMENT_ANALYSIS=true
ENABLE_TEXT_STATS=true
ENABLE_TEXT_TRANSFORMATION=true

# Logging
LOG_LEVEL=INFO
EOF

# Copy to actual .env
cp .env.example .env
```

## 🏗️ Core Agent Implementation

### **1. Agent Card Definition**

```python
# src/a2a_text_agent/text_agent.py
#!/usr/bin/env python3
"""
A2A Text Processing Agent
A text analysis and processing agent using the A2A Protocol SDK
"""

import asyncio
import os
import re
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
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

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


class TextProcessor:
    """Core text processing functionality."""
    
    @staticmethod
    def count_words(text: str) -> int:
        """Count words in text."""
        return len(text.split())
    
    @staticmethod
    def count_characters(text: str) -> int:
        """Count characters in text."""
        return len(text)
    
    @staticmethod
    def count_sentences(text: str) -> int:
        """Count sentences in text."""
        sentence_endings = r'[.!?]+\s*'
        sentences = re.split(sentence_endings, text.strip())
        return len([s for s in sentences if s.strip()])
    
    @staticmethod
    def to_uppercase(text: str) -> str:
        """Convert text to uppercase."""
        return text.upper()
    
    @staticmethod
    def to_lowercase(text: str) -> str:
        """Convert text to lowercase."""
        return text.lower()
    
    @staticmethod
    def reverse_text(text: str) -> str:
        """Reverse text."""
        return text[::-1]
    
    @staticmethod
    def extract_emails(text: str) -> List[str]:
        """Extract email addresses from text."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(email_pattern, text)
    
    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extract URLs from text."""
        url_pattern = r'https?://[^\s<>"{}|\\^`[\]]+[^\s<>"{}|\\^`[\].]'
        return re.findall(url_pattern, text)
    
    @staticmethod
    def simple_sentiment(text: str) -> str:
        """Simple rule-based sentiment analysis."""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'like', 'happy']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'sad', 'angry', 'frustrated']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"


class TextAgentExecutor(AgentExecutor):
    """A2A Text Agent Executor implementing text processing logic."""

    def __init__(self):
        super().__init__()
        self.processor = TextProcessor()
        logger.info("Text Agent Executor initialized")

    async def execute(self, task: Task, context: RequestContext) -> Optional[Message]:
        """Execute text processing task."""
        try:
            # Extract text from message parts
            text_content = ""
            if task.message and task.message.parts:
                text_parts = [part for part in task.message.parts if hasattr(part, 'text')]
                text_content = " ".join(part.text for part in text_parts)
            
            if not text_content.strip():
                return self._create_error_response(
                    task.message.message_id if task.message else "unknown",
                    "No text content provided for processing"
                )
            
            # Route to appropriate processing method
            response_text = await self._process_text_request(text_content.strip())
            
            # Create response message
            response_parts = [TextPart(text=response_text)]
            
            return Message(
                message_id=f"response-{datetime.now().isoformat()}",
                role="agent",
                parts=response_parts
            )
            
        except Exception as e:
            logger.error(f"Error in text processing execution: {e}")
            return self._create_error_response(
                task.message.message_id if task.message else "unknown",
                f"Processing error: {str(e)}"
            )

    async def _process_text_request(self, text: str) -> str:
        """Process text based on request content."""
        text_lower = text.lower()
        
        # Text statistics
        if any(word in text_lower for word in ['count', 'words', 'characters', 'sentences', 'stats', 'statistics']):
            return self._get_text_statistics(text)
        
        # Text transformations
        elif any(word in text_lower for word in ['uppercase', 'upper', 'caps']):
            return f"📝 Text: {self.processor.to_uppercase(text)}"
        
        elif any(word in text_lower for word in ['lowercase', 'lower']):
            return f"📝 Text: {self.processor.to_lowercase(text)}"
        
        elif 'reverse' in text_lower:
            return f"📝 Text: {self.processor.reverse_text(text)}"
        
        # Data extraction
        elif any(word in text_lower for word in ['extract', 'find', 'emails', 'email']):
            emails = self.processor.extract_emails(text)
            if emails:
                return f"📧 Emails found: {', '.join(emails)}"
            else:
                return "📧 No email addresses found"
        
        elif any(word in text_lower for word in ['extract', 'find', 'urls', 'links']):
            urls = self.processor.extract_urls(text)
            if urls:
                return f"🔗 URLs found: {', '.join(urls)}"
            else:
                return "🔗 No URLs found"
        
        # Sentiment analysis
        elif any(word in text_lower for word in ['sentiment', 'feeling', 'emotion']):
            sentiment = self.processor.simple_sentiment(text)
            return f"😊 Sentiment: {sentiment}"
        
        # Default: provide general text statistics
        else:
            return self._get_text_statistics(text)

    def _get_text_statistics(self, text: str) -> str:
        """Get comprehensive text statistics."""
        word_count = self.processor.count_words(text)
        char_count = self.processor.count_characters(text)
        sentence_count = self.processor.count_sentences(text)
        
        return f"📊 Text Stats: {word_count} words, {char_count} characters, {sentence_count} sentences"

    def _create_error_response(self, message_id: str, error_message: str) -> Message:
        """Create error response message."""
        response_parts = [TextPart(text=f"❌ Error: {error_message}")]
        
        return Message(
            message_id=f"error-{message_id}",
            role="agent", 
            parts=response_parts
        )


def create_agent_card() -> AgentCard:
    """Create the agent card describing text processing capabilities."""
    
    # Get configuration
    enable_sentiment = os.getenv("ENABLE_SENTIMENT_ANALYSIS", "true").lower() == "true"
    enable_stats = os.getenv("ENABLE_TEXT_STATS", "true").lower() == "true"
    enable_transform = os.getenv("ENABLE_TEXT_TRANSFORMATION", "true").lower() == "true"
    
    skills = []
    
    # Text statistics skill
    if enable_stats:
        skills.append(
            AgentSkill(
                id="text_statistics",
                name="Text Statistics",
                description="Analyze text and provide word count, character count, and sentence count",
                examples=[
                    "count words in this text",
                    "how many characters are in this sentence?",
                    "text statistics for this paragraph",
                    "analyze this text"
                ],
                tags=["statistics", "count", "analysis", "text"]
            )
        )
    
    # Text transformation skill
    if enable_transform:
        skills.append(
            AgentSkill(
                id="text_transformation", 
                name="Text Transformation",
                description="Transform text by changing case, reversing, or other modifications",
                examples=[
                    "convert to uppercase",
                    "make this lowercase", 
                    "reverse this text",
                    "transform this text"
                ],
                tags=["transformation", "uppercase", "lowercase", "reverse", "text"]
            )
        )
    
    # Data extraction skill
    skills.append(
        AgentSkill(
            id="data_extraction",
            name="Data Extraction", 
            description="Extract emails, URLs, and other structured data from text",
            examples=[
                "find emails in this text",
                "extract URLs from this content",
                "find email addresses",
                "get all links"
            ],
            tags=["extraction", "email", "url", "data", "parsing"]
        )
    )
    
    # Sentiment analysis skill
    if enable_sentiment:
        skills.append(
            AgentSkill(
                id="sentiment_analysis",
                name="Sentiment Analysis",
                description="Analyze text sentiment and determine if it's positive, negative, or neutral",
                examples=[
                    "what's the sentiment of this text?",
                    "analyze the feeling of this message",
                    "is this positive or negative?",
                    "sentiment analysis"
                ],
                tags=["sentiment", "emotion", "analysis", "positive", "negative", "neutral"]
            )
        )
    
    # Create agent description
    agent_name = os.getenv("AGENT_NAME", "A2A Text Processing Agent")
    agent_version = os.getenv("AGENT_VERSION", "0.1.0")
    agent_description = os.getenv("AGENT_DESCRIPTION", "A text analysis and processing agent using the A2A protocol")
    
    # Add capability summary to description
    capabilities = []
    if enable_stats:
        capabilities.append("text statistics")
    if enable_transform:
        capabilities.append("text transformation")
    if enable_sentiment:
        capabilities.append("sentiment analysis")
    capabilities.append("data extraction")
    
    full_description = f"{agent_description} with {', '.join(capabilities)} capabilities"
    
    return AgentCard(
        name=agent_name,
        description=full_description,
        version=agent_version,
        skills=skills,
        capabilities=AgentCapabilities(),
        default_input_modes=["text"],
        default_output_modes=["text"],
        url=f"http://localhost:{os.getenv('A2A_PORT', 8003)}"
    )


async def main():
    """Main entry point for the A2A Text Processing Agent."""
    
    # Configuration
    port = int(os.getenv("A2A_PORT", 8003))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting A2A Text Processing Agent on {host}:{port}")
    
    # Create components
    agent_executor = TextAgentExecutor()
    task_store = InMemoryTaskStore()
    queue_manager = InMemoryQueueManager()
    
    # Create request handler
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=task_store,
        queue_manager=queue_manager
    )
    
    # Create agent card
    agent_card = create_agent_card()
    
    logger.info(f"Agent card created with {len(agent_card.skills)} skills")
    
    # Create and configure FastAPI application
    app = A2AFastAPIApplication(
        request_handler=request_handler,
        agent_card=agent_card,
        title="A2A Text Processing Agent",
        description="Text analysis and processing agent using the A2A Protocol SDK"
    )
    
    # Configure and start server
    import uvicorn
    
    config = uvicorn.Config(
        app.app,
        host=host,
        port=port,
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
```

### **2. Testing Script**

```python
# scripts/test_agent.py
#!/usr/bin/env python3
"""
Test script for A2A Text Processing Agent
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any


class A2ATextAgentTester:
    """Test suite for A2A Text Processing Agent."""
    
    def __init__(self, base_url: str = "http://localhost:8003"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_agent_card(self) -> bool:
        """Test agent card retrieval."""
        print("🔍 Testing agent card retrieval...")
        
        try:
            async with self.session.get(f"{self.base_url}/.well-known/agent-card.json") as response:
                if response.status != 200:
                    print(f"❌ Agent card request failed with status {response.status}")
                    return False
                
                agent_card = await response.json()
                
                # Validate basic structure
                required_fields = ["name", "version", "description", "skills"]
                for field in required_fields:
                    if field not in agent_card:
                        print(f"❌ Missing required field: {field}")
                        return False
                
                print(f"✅ Agent card valid: {agent_card['name']} v{agent_card['version']}")
                print(f"   Skills: {len(agent_card['skills'])}")
                
                return True
                
        except Exception as e:
            print(f"❌ Agent card test failed: {e}")
            return False
    
    async def send_message(self, text: str) -> Dict[str, Any]:
        """Send A2A message to agent."""
        message_data = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "id": f"test-{asyncio.get_event_loop().time()}",
            "params": {
                "message": {
                    "messageId": f"msg-{asyncio.get_event_loop().time()}",
                    "role": "user",
                    "parts": [{"kind": "text", "text": text}]
                }
            }
        }
        
        async with self.session.post(
            self.base_url + "/",
            json=message_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            return await response.json()
    
    async def test_text_statistics(self) -> bool:
        """Test text statistics functionality."""
        print("\n📊 Testing text statistics...")
        
        test_text = "This is a test sentence. It has multiple sentences! How many words are there?"
        
        try:
            response = await self.send_message(f"count words in: {test_text}")
            
            if "result" not in response:
                print(f"❌ No result in response: {response}")
                return False
            
            result_text = response["result"]["parts"][0]["text"]
            print(f"✅ Text statistics response: {result_text}")
            
            # Check if response contains expected information
            if "words" in result_text and "characters" in result_text and "sentences" in result_text:
                return True
            else:
                print("❌ Response missing expected statistics")
                return False
                
        except Exception as e:
            print(f"❌ Text statistics test failed: {e}")
            return False
    
    async def test_text_transformation(self) -> bool:
        """Test text transformation functionality."""
        print("\n🔄 Testing text transformation...")
        
        test_cases = [
            ("convert to uppercase: hello world", "HELLO WORLD"),
            ("make this lowercase: HELLO WORLD", "hello world"),
            ("reverse this text: hello", "olleh")
        ]
        
        success_count = 0
        
        for test_input, expected_pattern in test_cases:
            try:
                response = await self.send_message(test_input)
                result_text = response["result"]["parts"][0]["text"]
                
                if expected_pattern.lower() in result_text.lower():
                    print(f"✅ Transformation test passed: {test_input[:20]}...")
                    success_count += 1
                else:
                    print(f"❌ Transformation test failed: {test_input[:20]}...")
                    print(f"   Expected pattern: {expected_pattern}")
                    print(f"   Got: {result_text}")
                    
            except Exception as e:
                print(f"❌ Transformation test error: {e}")
        
        return success_count == len(test_cases)
    
    async def test_data_extraction(self) -> bool:
        """Test data extraction functionality."""
        print("\n🔍 Testing data extraction...")
        
        test_text = "Contact us at support@example.com or visit https://www.example.com for more info"
        
        # Test email extraction
        try:
            response = await self.send_message(f"find emails in: {test_text}")
            result_text = response["result"]["parts"][0]["text"]
            
            if "support@example.com" in result_text:
                print("✅ Email extraction test passed")
            else:
                print(f"❌ Email extraction failed: {result_text}")
                return False
                
        except Exception as e:
            print(f"❌ Email extraction test error: {e}")
            return False
        
        # Test URL extraction
        try:
            response = await self.send_message(f"find URLs in: {test_text}")
            result_text = response["result"]["parts"][0]["text"]
            
            if "https://www.example.com" in result_text:
                print("✅ URL extraction test passed")
                return True
            else:
                print(f"❌ URL extraction failed: {result_text}")
                return False
                
        except Exception as e:
            print(f"❌ URL extraction test error: {e}")
            return False
    
    async def test_sentiment_analysis(self) -> bool:
        """Test sentiment analysis functionality."""
        print("\n😊 Testing sentiment analysis...")
        
        test_cases = [
            ("This is a wonderful and amazing day!", "positive"),
            ("I hate this terrible experience", "negative"),
            ("This is just a normal sentence", "neutral")
        ]
        
        success_count = 0
        
        for test_text, expected_sentiment in test_cases:
            try:
                response = await self.send_message(f"analyze sentiment: {test_text}")
                result_text = response["result"]["parts"][0]["text"]
                
                if expected_sentiment.lower() in result_text.lower():
                    print(f"✅ Sentiment test passed: {expected_sentiment}")
                    success_count += 1
                else:
                    print(f"❌ Sentiment test failed: expected {expected_sentiment}")
                    print(f"   Got: {result_text}")
                    
            except Exception as e:
                print(f"❌ Sentiment test error: {e}")
        
        return success_count >= 2  # Allow some flexibility
    
    async def test_error_handling(self) -> bool:
        """Test error handling."""
        print("\n❌ Testing error handling...")
        
        try:
            # Test empty message
            response = await self.send_message("")
            result_text = response["result"]["parts"][0]["text"]
            
            if "error" in result_text.lower() or "no text" in result_text.lower():
                print("✅ Error handling test passed")
                return True
            else:
                print(f"❌ Error handling test failed: {result_text}")
                return False
                
        except Exception as e:
            print(f"❌ Error handling test error: {e}")
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all test suites."""
        print("🚀 Starting A2A Text Processing Agent Tests\n")
        
        tests = [
            ("Agent Card", self.test_agent_card),
            ("Text Statistics", self.test_text_statistics),
            ("Text Transformation", self.test_text_transformation),
            ("Data Extraction", self.test_data_extraction), 
            ("Sentiment Analysis", self.test_sentiment_analysis),
            ("Error Handling", self.test_error_handling)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if await test_func():
                    passed += 1
            except Exception as e:
                print(f"❌ {test_name} test crashed: {e}")
        
        print(f"\n📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed")
            return False


async def main():
    """Run the test suite."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test A2A Text Processing Agent")
    parser.add_argument("--url", default="http://localhost:8003", help="Agent base URL")
    
    args = parser.parse_args()
    
    async with A2ATextAgentTester(args.url) as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
```

### **3. Deployment Scripts**

```bash
# scripts/start_agent.py
#!/usr/bin/env python3
"""
Start script for A2A Text Processing Agent
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from a2a_text_agent.text_agent import main

if __name__ == "__main__":
    # Ensure we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Not running in a virtual environment")
        print("   Consider activating your virtual environment first:")
        print("   source venv/bin/activate")
        print()
    
    print("🚀 Starting A2A Text Processing Agent...")
    
    # Run the agent
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Agent stopped by user")
    except Exception as e:
        print(f"❌ Agent failed to start: {e}")
        sys.exit(1)
```

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY .env.example .env

# Expose port
EXPOSE 8003

# Set Python path
ENV PYTHONPATH=/app/src

# Run the agent
CMD ["python", "scripts/start_agent.py"]
```

## 🧪 Testing and Validation

### **1. Manual Testing**

```bash
# Start the agent
source venv/bin/activate
python scripts/start_agent.py

# In another terminal, test the agent
python scripts/test_agent.py
```

### **2. Individual Feature Testing**

```bash
# Test agent discovery
curl -s http://localhost:8003/.well-known/agent-card.json | jq '{
  name,
  version,
  skills: [.skills[] | {id, name}]
}'

# Test text statistics
curl -s -X POST http://localhost:8003/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "id": "test-stats",
    "params": {
      "message": {
        "messageId": "msg-stats",
        "role": "user",
        "parts": [{"kind": "text", "text": "count words in this sentence"}]
      }
    }
  }' | jq -r '.result.parts[0].text'

# Test text transformation
curl -s -X POST http://localhost:8003/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "id": "test-transform", 
    "params": {
      "message": {
        "messageId": "msg-transform",
        "role": "user",
        "parts": [{"kind": "text", "text": "convert to uppercase: hello world"}]
      }
    }
  }' | jq -r '.result.parts[0].text'

# Test data extraction
curl -s -X POST http://localhost:8003/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "id": "test-extract",
    "params": {
      "message": {
        "messageId": "msg-extract", 
        "role": "user",
        "parts": [{"kind": "text", "text": "find emails in: contact us at test@example.com"}]
      }
    }
  }' | jq -r '.result.parts[0].text'

# Test sentiment analysis
curl -s -X POST http://localhost:8003/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send", 
    "id": "test-sentiment",
    "params": {
      "message": {
        "messageId": "msg-sentiment",
        "role": "user",
        "parts": [{"kind": "text", "text": "analyze sentiment: I love this amazing product!"}]
      }
    }
  }' | jq -r '.result.parts[0].text'
```

### **3. Integration Testing**

```python
# tests/test_integration.py
import pytest
import asyncio
import aiohttp
from typing import Dict, Any


class TestA2ATextAgent:
    """Integration tests for A2A Text Agent."""
    
    BASE_URL = "http://localhost:8003"
    
    async def send_message(self, text: str) -> Dict[str, Any]:
        """Helper to send A2A message."""
        message_data = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "id": "test-id",
            "params": {
                "message": {
                    "messageId": "test-msg",
                    "role": "user",
                    "parts": [{"kind": "text", "text": text}]
                }
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.BASE_URL}/",
                json=message_data
            ) as response:
                return await response.json()
    
    @pytest.mark.asyncio
    async def test_agent_card_available(self):
        """Test that agent card is available."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.BASE_URL}/.well-known/agent-card.json") as response:
                assert response.status == 200
                data = await response.json()
                assert "name" in data
                assert "skills" in data
    
    @pytest.mark.asyncio
    async def test_text_statistics(self):
        """Test text statistics functionality."""
        response = await self.send_message("count words in: hello world test")
        
        assert "result" in response
        result_text = response["result"]["parts"][0]["text"]
        assert "words" in result_text.lower()
        assert "3" in result_text  # Should count 3 words
    
    @pytest.mark.asyncio
    async def test_text_transformation(self):
        """Test text transformation functionality."""
        response = await self.send_message("convert to uppercase: hello")
        
        assert "result" in response
        result_text = response["result"]["parts"][0]["text"]
        assert "HELLO" in result_text
    
    @pytest.mark.asyncio
    async def test_email_extraction(self):
        """Test email extraction functionality."""
        response = await self.send_message("find emails in: contact test@example.com")
        
        assert "result" in response
        result_text = response["result"]["parts"][0]["text"]
        assert "test@example.com" in result_text
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling for empty input."""
        response = await self.send_message("")
        
        assert "result" in response
        result_text = response["result"]["parts"][0]["text"]
        assert "error" in result_text.lower() or "no text" in result_text.lower()


# Run with: pytest tests/test_integration.py -v
```

## 🚀 Docker Deployment

### **1. Build and Run**

```bash
# Build Docker image
docker build -t a2a-text-agent .

# Run container
docker run -d -p 8003:8003 --name text-agent a2a-text-agent

# Test container
curl -s http://localhost:8003/.well-known/agent-card.json | jq .name

# View logs
docker logs text-agent

# Stop and cleanup
docker stop text-agent && docker rm text-agent
```

### **2. Docker Compose Integration**

```yaml
# docker-compose.yml addition
services:
  a2a-text-agent:
    build:
      context: ./a2a-text-agent
      dockerfile: Dockerfile
    ports:
      - "8003:8003"
    networks:
      - agent-network
    labels:
      - "agent.protocol=a2a"
      - "agent.type=text"
      - "agent.version=0.1.0" 
      - "agent.capabilities=text-processing,statistics,transformation,extraction,sentiment"
    environment:
      - A2A_PORT=8003
      - ENABLE_SENTIMENT_ANALYSIS=true
      - ENABLE_TEXT_STATS=true
      - ENABLE_TEXT_TRANSFORMATION=true
      - LOG_LEVEL=INFO
```

## 🔧 Orchestrator Integration

### **1. Discovery Configuration**

Update the orchestrator to discover your text agent:

```python
# In agents/orchestrator/src/orchestrator/discovery.py
known_endpoints = [
    # Existing agents...
    {"url": "http://a2a-text-agent:8003", "protocol": "a2a", "name": "text"},
    {"url": "http://localhost:8003", "protocol": "a2a", "name": "text"}  # fallback
]
```

### **2. Testing Orchestrator Integration**

```bash
# Start all agents including orchestrator
docker-compose up -d

# Test discovery through orchestrator
curl -s http://localhost:8004/agents | jq '.agents[] | select(.protocol == "a2a")'

# Test routing through orchestrator  
curl -s -X POST http://localhost:8004/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "count words in this text message",
    "agent_type": "a2a",
    "agent_name": "text"
  }' | jq '.response'
```

## 📊 Performance and Monitoring

### **1. Performance Testing**

```python
# scripts/performance_test.py
import asyncio
import aiohttp
import time
from statistics import mean, median


async def performance_test(base_url: str = "http://localhost:8003", concurrent: int = 10, requests: int = 100):
    """Run performance test on text agent."""
    
    async def send_request(session, request_id):
        start_time = time.time()
        
        try:
            message_data = {
                "jsonrpc": "2.0",
                "method": "message/send",
                "id": f"perf-{request_id}",
                "params": {
                    "message": {
                        "messageId": f"msg-{request_id}",
                        "role": "user",
                        "parts": [{"kind": "text", "text": "count words in this performance test message"}]
                    }
                }
            }
            
            async with session.post(f"{base_url}/", json=message_data) as response:
                await response.json()
                
            return time.time() - start_time
            
        except Exception as e:
            print(f"Request {request_id} failed: {e}")
            return None
    
    # Run concurrent requests
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(concurrent)
        
        async def bounded_request(request_id):
            async with semaphore:
                return await send_request(session, request_id)
        
        print(f"Running {requests} requests with {concurrent} concurrent connections...")
        
        start_time = time.time()
        results = await asyncio.gather(*[bounded_request(i) for i in range(requests)])
        total_time = time.time() - start_time
        
        # Filter successful requests
        successful_times = [r for r in results if r is not None]
        
        if successful_times:
            print(f"Results:")
            print(f"  Total time: {total_time:.2f}s")
            print(f"  Successful requests: {len(successful_times)}/{requests}")
            print(f"  Requests per second: {len(successful_times)/total_time:.2f}")
            print(f"  Average response time: {mean(successful_times)*1000:.2f}ms")
            print(f"  Median response time: {median(successful_times)*1000:.2f}ms")
            print(f"  Min response time: {min(successful_times)*1000:.2f}ms")
            print(f"  Max response time: {max(successful_times)*1000:.2f}ms")


if __name__ == "__main__":
    asyncio.run(performance_test())
```

### **2. Health Monitoring**

```python
# Add to text_agent.py
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "agent_name": os.getenv("AGENT_NAME", "A2A Text Processing Agent"),
        "version": os.getenv("AGENT_VERSION", "0.1.0"),
        "skills_enabled": len(create_agent_card().skills)
    }
```

## 🎯 Key Implementation Patterns

### **1. Skill-Based Routing**

```python
# Pattern: Route messages based on content analysis
async def _process_text_request(self, text: str) -> str:
    text_lower = text.lower()
    
    # Use keywords to determine processing type
    if any(word in text_lower for word in ['count', 'words', 'stats']):
        return self._get_text_statistics(text)
    elif 'uppercase' in text_lower:
        return f"📝 Text: {self.processor.to_uppercase(text)}"
    # ... more routing logic
```

### **2. Error Handling**

```python
# Pattern: Comprehensive error handling with user-friendly messages
try:
    result = await self._process_text_request(text_content.strip())
    return self._create_success_response(result)
except ValidationError as e:
    return self._create_error_response("validation_error", f"Input validation failed: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return self._create_error_response("processing_error", "An unexpected error occurred")
```

### **3. Configuration-Driven Features**

```python
# Pattern: Enable/disable features via environment variables
def create_agent_card() -> AgentCard:
    skills = []
    
    if os.getenv("ENABLE_TEXT_STATS", "true").lower() == "true":
        skills.append(create_stats_skill())
    
    if os.getenv("ENABLE_SENTIMENT_ANALYSIS", "true").lower() == "true":
        skills.append(create_sentiment_skill())
    
    return AgentCard(skills=skills, ...)
```

## 🎓 Learning Exercises

### **Exercise 1: Add New Skill**

Add a "text summarization" skill to your agent:

```python
# Add to TextProcessor class
@staticmethod
def simple_summary(text: str, sentences: int = 3) -> str:
    """Create a simple extractive summary."""
    sentences_list = re.split(r'[.!?]+', text)
    sentences_list = [s.strip() for s in sentences_list if s.strip()]
    
    # Simple scoring: prefer sentences with more words
    scored = [(len(s.split()), s) for s in sentences_list]
    scored.sort(reverse=True)
    
    # Take top sentences
    summary_sentences = [s[1] for s in scored[:sentences]]
    return ". ".join(summary_sentences) + "."

# Add to routing logic
elif any(word in text_lower for word in ['summary', 'summarize']):
    return f"📄 Summary: {self.processor.simple_summary(text)}"

# Add skill to agent card
AgentSkill(
    id="text_summarization",
    name="Text Summarization",
    description="Create a brief summary of longer text",
    examples=["summarize this article", "create a summary"],
    tags=["summarization", "text", "extraction"]
)
```

### **Exercise 2: Multi-Language Support**

Add language detection and processing:

```python
# Install additional dependency: pip install langdetect

from langdetect import detect

@staticmethod
def detect_language(text: str) -> str:
    """Detect text language."""
    try:
        return detect(text)
    except:
        return "unknown"

# Add to routing and skills
```

### **Exercise 3: Advanced Data Extraction**

Add phone number and date extraction:

```python
@staticmethod
def extract_phone_numbers(text: str) -> List[str]:
    """Extract phone numbers from text."""
    phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    return re.findall(phone_pattern, text)

@staticmethod
def extract_dates(text: str) -> List[str]:
    """Extract dates from text."""
    date_pattern = r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b'
    return re.findall(date_pattern, text)
```

## 🎯 Key Takeaways

### **🔑 A2A Agent Essentials**
1. **SDK Integration**: Use the A2A SDK for proper protocol compliance
2. **Agent Card**: Dynamic agent cards that reflect current capabilities
3. **Message Handling**: Robust parsing of A2A message parts
4. **Skill-Based Logic**: Route processing based on advertised skills
5. **Error Handling**: Comprehensive error handling with user-friendly messages

### **🚀 Implementation Best Practices**
- **Async Processing**: Use async/await for all I/O operations
- **Configuration Driven**: Enable/disable features via environment variables
- **Comprehensive Testing**: Include unit, integration, and performance tests
- **Docker Ready**: Containerize for easy deployment
- **Monitoring**: Include health checks and performance metrics

### **🛠️ Development Patterns**
- **Text Processing**: Break complex text processing into focused methods
- **Response Formatting**: Consistent, emoji-enhanced response formats
- **Feature Flags**: Use environment variables to control capabilities
- **Graceful Degradation**: Handle missing dependencies gracefully

## ⏭️ Next Steps

In [Part 4: Advanced A2A Features](./04-advanced-features.md), we'll explore:
- Streaming responses and real-time processing
- Multi-part message handling and complex data types
- Advanced error handling and recovery patterns
- Performance optimization and caching strategies
- Integration with external services and APIs
- Production deployment and monitoring

You've successfully built your first A2A agent! Ready for advanced features?

---

*This tutorial is part of the Agent Network Sandbox educational series. The Text Processing Agent demonstrates real-world A2A implementation patterns using the official A2A SDK.*