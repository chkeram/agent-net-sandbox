# Part 4: Advanced A2A Features

## 🎯 Learning Objectives

By the end of this tutorial, you will:
- Implement streaming responses and real-time processing
- Handle multi-part messages and complex data types
- Master advanced error handling and recovery patterns
- Optimize performance with caching and async patterns
- Integrate with external services and APIs
- Deploy to production with monitoring and observability

## 📚 Prerequisites

- Completed [Part 1: Understanding A2A Fundamentals](./01-understanding-a2a.md)
- Completed [Part 2: Configuration & Discovery](./02-configuration-discovery.md)
- Completed [Part 3: Building Your First A2A Agent](./03-building-first-agent.md)
- Understanding of async Python, caching, and monitoring concepts
- Access to production-ready deployment environment

## 🌊 Streaming Responses

A2A protocol supports streaming responses for long-running operations. Let's enhance our Math Agent with streaming capabilities:

### **1. Streaming Implementation**

```python
# Enhanced math_agent.py with streaming
import asyncio
from typing import AsyncGenerator
from a2a.types import MessagePart, TextPart

class StreamingMathAgent(AgentExecutor):
    """Math agent with streaming response capabilities."""
    
    async def execute_streaming(self, task: Task, context: RequestContext) -> AsyncGenerator[MessagePart, None]:
        """Execute with streaming response."""
        try:
            text_content = self._extract_text(task.message)
            
            if self._is_complex_calculation(text_content):
                # Stream the calculation process
                async for part in self._stream_complex_calculation(text_content):
                    yield part
            else:
                # Simple calculation - return single response
                result = await self._process_simple_calculation(text_content)
                yield TextPart(text=result)
                
        except Exception as e:
            yield TextPart(text=f"❌ Error: {str(e)}")
    
    def _is_complex_calculation(self, text: str) -> bool:
        """Determine if calculation requires streaming."""
        complex_keywords = ['prime factors', 'fibonacci', 'factorial', 'series', 'sequence']
        return any(keyword in text.lower() for keyword in complex_keywords)
    
    async def _stream_complex_calculation(self, text: str) -> AsyncGenerator[TextPart, None]:
        """Stream complex calculation steps."""
        if 'fibonacci' in text.lower():
            # Extract number from text (simplified)
            import re
            numbers = re.findall(r'\d+', text)
            if numbers:
                n = int(numbers[0])
                yield TextPart(text=f"🔄 Calculating Fibonacci sequence up to {n}...")
                
                # Stream Fibonacci calculation
                a, b = 0, 1
                sequence = []
                
                for i in range(min(n, 20)):  # Limit for demo
                    sequence.append(a)
                    if i % 5 == 0 and i > 0:  # Stream every 5 numbers
                        yield TextPart(text=f"📊 Progress: {', '.join(map(str, sequence))}")
                        await asyncio.sleep(0.1)  # Simulate processing time
                    a, b = b, a + b
                
                yield TextPart(text=f"✅ Fibonacci({n}): {', '.join(map(str, sequence))}")
        
        elif 'prime factors' in text.lower():
            # Stream prime factorization
            numbers = re.findall(r'\d+', text)
            if numbers:
                n = int(numbers[0])
                yield TextPart(text=f"🔄 Finding prime factors of {n}...")
                
                factors = []
                d = 2
                temp_n = n
                
                while d * d <= temp_n:
                    while temp_n % d == 0:
                        factors.append(d)
                        temp_n //= d
                        yield TextPart(text=f"📊 Found factor: {d}, remaining: {temp_n}")
                        await asyncio.sleep(0.1)
                    d += 1
                
                if temp_n > 1:
                    factors.append(temp_n)
                
                yield TextPart(text=f"✅ Prime factors of {n}: {' × '.join(map(str, factors))}")
```

### **2. WebSocket Streaming Support**

```python
# Enhanced FastAPI app with WebSocket streaming
from fastapi import WebSocket, WebSocketDisconnect
import json

class StreamingA2AApp(A2AFastAPIApplication):
    """A2A application with WebSocket streaming support."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_websocket_routes()
    
    def setup_websocket_routes(self):
        @self.app.websocket("/stream")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            
            try:
                while True:
                    # Receive A2A message via WebSocket
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    # Create task from WebSocket message
                    task = self._create_task_from_websocket(message_data)
                    
                    # Stream response
                    if hasattr(self.request_handler.agent_executor, 'execute_streaming'):
                        async for part in self.request_handler.agent_executor.execute_streaming(task, None):
                            await websocket.send_text(json.dumps({
                                "type": "message_part",
                                "part": part.dict()
                            }))
                    
                    await websocket.send_text(json.dumps({"type": "complete"}))
                    
            except WebSocketDisconnect:
                pass
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "error": str(e)
                }))

# WebSocket client test
async def test_websocket_streaming():
    import websockets
    import json
    
    uri = "ws://localhost:8002/stream"
    async with websockets.connect(uri) as websocket:
        # Send streaming request
        message = {
            "message": {
                "messageId": "stream-test",
                "role": "user",
                "parts": [{"kind": "text", "text": "fibonacci 10"}]
            }
        }
        
        await websocket.send(json.dumps(message))
        
        # Receive streaming responses
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            
            if data["type"] == "complete":
                break
            elif data["type"] == "message_part":
                print(f"Streamed: {data['part']['text']}")
            elif data["type"] == "error":
                print(f"Error: {data['error']}")
                break
```

## 🧩 Multi-Part Message Handling

A2A supports complex multi-part messages with different content types:

### **1. Multi-Part Message Processor**

```python
# Enhanced message processing for multi-part content
from a2a.types import ImagePart, FilePart, DataPart

class MultiPartProcessor:
    """Process multi-part A2A messages."""
    
    async def process_multipart_message(self, message: Message) -> str:
        """Process message with multiple parts."""
        results = []
        
        for i, part in enumerate(message.parts):
            result = await self._process_single_part(part, i)
            results.append(result)
        
        return self._combine_results(results)
    
    async def _process_single_part(self, part: MessagePart, index: int) -> str:
        """Process individual message part."""
        if isinstance(part, TextPart):
            return await self._process_text_part(part, index)
        elif isinstance(part, ImagePart):
            return await self._process_image_part(part, index)
        elif isinstance(part, FilePart):
            return await self._process_file_part(part, index)
        elif isinstance(part, DataPart):
            return await self._process_data_part(part, index)
        else:
            return f"⚠️ Unsupported part type: {type(part).__name__}"
    
    async def _process_text_part(self, part: TextPart, index: int) -> str:
        """Process text part."""
        text = part.text.strip()
        
        # Analyze text content
        if self._contains_math(text):
            return await self._process_math_text(text)
        elif self._contains_question(text):
            return f"❓ Question detected in part {index + 1}: {text[:50]}..."
        else:
            return f"📝 Text part {index + 1}: {len(text)} characters"
    
    async def _process_image_part(self, part: ImagePart, index: int) -> str:
        """Process image part (future implementation)."""
        # Placeholder for image processing
        return f"🖼️ Image part {index + 1}: {part.content_type or 'unknown format'}"
    
    async def _process_file_part(self, part: FilePart, index: int) -> str:
        """Process file part (future implementation)."""
        return f"📎 File part {index + 1}: {part.filename or 'unnamed file'}"
    
    async def _process_data_part(self, part: DataPart, index: int) -> str:
        """Process structured data part."""
        if hasattr(part, 'data') and isinstance(part.data, dict):
            keys = list(part.data.keys())
            return f"📊 Data part {index + 1}: {len(keys)} fields ({', '.join(keys[:3])}{'...' if len(keys) > 3 else ''})"
        else:
            return f"📊 Data part {index + 1}: structured data"
    
    def _combine_results(self, results: List[str]) -> str:
        """Combine processing results."""
        if len(results) == 1:
            return results[0]
        else:
            combined = "🧩 Multi-part message processed:\n"
            combined += "\n".join(f"  {i+1}. {result}" for i, result in enumerate(results))
            return combined

# Usage in agent executor
class AdvancedMathAgent(AgentExecutor):
    def __init__(self):
        super().__init__()
        self.multipart_processor = MultiPartProcessor()
    
    async def execute(self, task: Task, context: RequestContext) -> Optional[Message]:
        """Execute with multi-part support."""
        if len(task.message.parts) > 1:
            # Handle multi-part message
            result = await self.multipart_processor.process_multipart_message(task.message)
        else:
            # Handle single-part message (existing logic)
            result = await self._process_single_part_message(task.message)
        
        return Message(
            message_id=f"response-{datetime.now().isoformat()}",
            role="agent",
            parts=[TextPart(text=result)]
        )
```

### **2. Complex Data Handling**

```python
# Handle structured data in A2A messages
class StructuredDataProcessor:
    """Process structured data in A2A messages."""
    
    async def process_math_data(self, data: Dict[str, Any]) -> str:
        """Process mathematical data structures."""
        if 'matrix' in data:
            return await self._process_matrix(data['matrix'])
        elif 'equation' in data:
            return await self._process_equation(data['equation'])
        elif 'dataset' in data:
            return await self._process_dataset(data['dataset'])
        else:
            return "📊 Structured data processed"
    
    async def _process_matrix(self, matrix: List[List[float]]) -> str:
        """Process matrix operations."""
        rows, cols = len(matrix), len(matrix[0]) if matrix else 0
        
        # Calculate basic matrix properties
        total_elements = rows * cols
        matrix_sum = sum(sum(row) for row in matrix)
        
        return f"🔢 Matrix Analysis: {rows}×{cols} matrix, {total_elements} elements, sum={matrix_sum}"
    
    async def _process_equation(self, equation: Dict[str, Any]) -> str:
        """Process equation data."""
        eq_type = equation.get('type', 'unknown')
        variables = equation.get('variables', [])
        
        return f"📐 Equation: {eq_type} with variables {', '.join(variables)}"
    
    async def _process_dataset(self, dataset: List[Dict[str, Any]]) -> str:
        """Process statistical dataset."""
        if not dataset:
            return "📊 Empty dataset"
        
        size = len(dataset)
        fields = list(dataset[0].keys()) if dataset else []
        
        # Basic statistics
        if 'value' in fields:
            values = [item.get('value', 0) for item in dataset if isinstance(item.get('value'), (int, float))]
            if values:
                avg = sum(values) / len(values)
                return f"📊 Dataset: {size} records, average value: {avg:.2f}"
        
        return f"📊 Dataset: {size} records with fields {', '.join(fields)}"
```

## 🚀 Performance Optimization

### **1. Caching Implementation**

```python
# Redis-based caching for improved performance
import redis
import json
import hashlib
from typing import Optional

class A2ACache:
    """Caching layer for A2A agent responses."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.default_ttl = 3600  # 1 hour
    
    def _generate_cache_key(self, message: Message) -> str:
        """Generate cache key from message content."""
        # Create hash from message parts
        content = ""
        for part in message.parts:
            if isinstance(part, TextPart):
                content += part.text
        
        return f"a2a:response:{hashlib.md5(content.encode()).hexdigest()}"
    
    async def get_cached_response(self, message: Message) -> Optional[str]:
        """Get cached response for message."""
        cache_key = self._generate_cache_key(message)
        
        try:
            cached = self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            print(f"Cache get error: {e}")
        
        return None
    
    async def cache_response(self, message: Message, response: str, ttl: Optional[int] = None):
        """Cache response for message."""
        cache_key = self._generate_cache_key(message)
        ttl = ttl or self.default_ttl
        
        try:
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(response)
            )
        except Exception as e:
            print(f"Cache set error: {e}")
    
    def should_cache(self, message: Message) -> bool:
        """Determine if message should be cached."""
        # Cache deterministic math operations, not LLM responses
        text_content = " ".join(
            part.text for part in message.parts 
            if isinstance(part, TextPart)
        ).lower()
        
        # Don't cache requests with current time, random numbers, etc.
        non_cacheable = ['now', 'today', 'current', 'random', 'time']
        return not any(word in text_content for word in non_cacheable)

# Enhanced agent with caching
class CachedMathAgent(AgentExecutor):
    def __init__(self):
        super().__init__()
        self.cache = A2ACache()
        self.processor = MathOperations()
    
    async def execute(self, task: Task, context: RequestContext) -> Optional[Message]:
        """Execute with caching support."""
        # Check cache first
        if self.cache.should_cache(task.message):
            cached_response = await self.cache.get_cached_response(task.message)
            if cached_response:
                return Message(
                    message_id=f"cached-{datetime.now().isoformat()}",
                    role="agent",
                    parts=[TextPart(text=f"💾 {cached_response}")]
                )
        
        # Process request
        response = await self._process_request(task.message)
        
        # Cache response if appropriate
        if self.cache.should_cache(task.message):
            await self.cache.cache_response(task.message, response)
        
        return Message(
            message_id=f"response-{datetime.now().isoformat()}",
            role="agent",
            parts=[TextPart(text=response)]
        )
```

### **2. Async Optimization Patterns**

```python
# Optimized async patterns for better performance
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

class OptimizedMathAgent(AgentExecutor):
    """Math agent with performance optimizations."""
    
    def __init__(self):
        super().__init__()
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.semaphore = asyncio.Semaphore(10)  # Limit concurrent operations
    
    async def execute(self, task: Task, context: RequestContext) -> Optional[Message]:
        """Execute with performance optimizations."""
        async with self.semaphore:  # Limit concurrency
            start_time = time.time()
            
            try:
                # Process with timeout
                response = await asyncio.wait_for(
                    self._process_with_timeout(task.message),
                    timeout=30.0
                )
                
                processing_time = time.time() - start_time
                response += f" (processed in {processing_time:.3f}s)"
                
                return Message(
                    message_id=f"response-{datetime.now().isoformat()}",
                    role="agent",
                    parts=[TextPart(text=response)]
                )
                
            except asyncio.TimeoutError:
                return self._create_timeout_response(task.message.message_id)
            except Exception as e:
                return self._create_error_response(task.message.message_id, str(e))
    
    async def _process_with_timeout(self, message: Message) -> str:
        """Process message with timeout and optimization."""
        text_content = self._extract_text(message)
        
        # Determine processing strategy
        if self._is_cpu_intensive(text_content):
            # Use thread pool for CPU-intensive operations
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.thread_pool,
                self._cpu_intensive_calculation,
                text_content
            )
        else:
            # Use async processing for I/O or simple operations
            return await self._async_calculation(text_content)
    
    def _cpu_intensive_calculation(self, text: str) -> str:
        """CPU-intensive calculation in thread pool."""
        # Example: Large prime factorization
        if 'prime factors' in text.lower():
            # Extract number and calculate prime factors
            import re
            numbers = re.findall(r'\d+', text)
            if numbers:
                n = int(numbers[0])
                factors = self._calculate_prime_factors(n)
                return f"🔢 Prime factors of {n}: {' × '.join(map(str, factors))}"
        
        return "🧮 CPU-intensive calculation completed"
    
    def _calculate_prime_factors(self, n: int) -> List[int]:
        """Calculate prime factors (CPU-intensive)."""
        factors = []
        d = 2
        while d * d <= n:
            while n % d == 0:
                factors.append(d)
                n //= d
            d += 1
        if n > 1:
            factors.append(n)
        return factors
    
    async def _async_calculation(self, text: str) -> str:
        """Fast async calculation."""
        # Handle simple operations asynchronously
        return await self._process_simple_math(text)
```

## 🔗 External Service Integration

### **1. API Integration**

```python
# Integration with external mathematical services
import aiohttp
from typing import Dict, Any

class ExternalServiceIntegrator:
    """Integrate with external mathematical APIs."""
    
    def __init__(self):
        self.wolfram_alpha_key = os.getenv("WOLFRAM_ALPHA_API_KEY")
        self.math_api_base = "https://api.mathjs.org/v4/"
    
    async def query_wolfram_alpha(self, query: str) -> Optional[str]:
        """Query Wolfram Alpha API."""
        if not self.wolfram_alpha_key:
            return None
        
        url = "http://api.wolframalpha.com/v1/result"
        params = {
            "appid": self.wolfram_alpha_key,
            "i": query
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        result = await response.text()
                        return f"🐺 Wolfram: {result}"
        except Exception as e:
            print(f"Wolfram Alpha API error: {e}")
        
        return None
    
    async def query_math_api(self, expression: str) -> Optional[str]:
        """Query Math.js API."""
        url = f"{self.math_api_base}?expr={expression}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.text()
                        return f"📊 MathJS: {result}"
        except Exception as e:
            print(f"Math API error: {e}")
        
        return None
    
    async def get_enhanced_result(self, query: str) -> str:
        """Get result from multiple sources."""
        # Try multiple services in parallel
        tasks = [
            self.query_wolfram_alpha(query),
            self.query_math_api(query)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Return first successful result
        for result in results:
            if isinstance(result, str) and result:
                return result
        
        return "🔍 No external results available"

# Enhanced agent with external integrations
class IntegratedMathAgent(AgentExecutor):
    def __init__(self):
        super().__init__()
        self.external_services = ExternalServiceIntegrator()
        self.local_processor = MathOperations()
    
    async def execute(self, task: Task, context: RequestContext) -> Optional[Message]:
        """Execute with external service integration."""
        text_content = self._extract_text(task.message)
        
        # Determine if we should use external services
        if self._should_use_external_service(text_content):
            external_result = await self.external_services.get_enhanced_result(text_content)
            if "No external results" not in external_result:
                response = external_result
            else:
                # Fall back to local processing
                response = await self._process_locally(text_content)
        else:
            # Use local processing
            response = await self._process_locally(text_content)
        
        return Message(
            message_id=f"response-{datetime.now().isoformat()}",
            role="agent",
            parts=[TextPart(text=response)]
        )
    
    def _should_use_external_service(self, text: str) -> bool:
        """Determine if external services should be used."""
        complex_keywords = [
            'integral', 'derivative', 'limit', 'series', 'complex analysis',
            'differential equation', 'linear algebra', 'calculus'
        ]
        return any(keyword in text.lower() for keyword in complex_keywords)
```

### **2. Database Integration**

```python
# Database integration for persistent storage
import asyncpg
from typing import List, Dict, Any

class MathHistoryStore:
    """Store and retrieve mathematical computation history."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
    
    async def initialize(self):
        """Initialize database connection pool."""
        self.pool = await asyncpg.create_pool(self.database_url)
        await self._create_tables()
    
    async def _create_tables(self):
        """Create required database tables."""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS math_queries (
                    id SERIAL PRIMARY KEY,
                    query_text TEXT NOT NULL,
                    result_text TEXT NOT NULL,
                    processing_time FLOAT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    agent_version TEXT
                )
            ''')
    
    async def store_query(self, query: str, result: str, processing_time: float):
        """Store query and result."""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO math_queries (query_text, result_text, processing_time, agent_version)
                VALUES ($1, $2, $3, $4)
            ''', query, result, processing_time, "0.1.0")
    
    async def get_similar_queries(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar historical queries."""
        async with self.pool.acquire() as conn:
            # Simple similarity search using text similarity
            rows = await conn.fetch('''
                SELECT query_text, result_text, timestamp
                FROM math_queries
                WHERE query_text ILIKE $1
                ORDER BY timestamp DESC
                LIMIT $2
            ''', f"%{query[:20]}%", limit)
            
            return [dict(row) for row in rows]

# Agent with database integration
class PersistentMathAgent(AgentExecutor):
    def __init__(self):
        super().__init__()
        self.history_store = MathHistoryStore(os.getenv("DATABASE_URL", "postgresql://localhost/math_agent"))
    
    async def initialize(self):
        """Initialize agent components."""
        await self.history_store.initialize()
    
    async def execute(self, task: Task, context: RequestContext) -> Optional[Message]:
        """Execute with history tracking."""
        start_time = time.time()
        text_content = self._extract_text(task.message)
        
        # Check for similar historical queries
        similar = await self.history_store.get_similar_queries(text_content)
        if similar:
            # Provide context from history
            history_context = f"📚 Found {len(similar)} similar queries in history. "
        else:
            history_context = ""
        
        # Process the query
        response = await self._process_math_request(text_content)
        processing_time = time.time() - start_time
        
        # Store in history
        await self.history_store.store_query(text_content, response, processing_time)
        
        # Add history context to response
        full_response = f"{history_context}{response}"
        
        return Message(
            message_id=f"response-{datetime.now().isoformat()}",
            role="agent",
            parts=[TextPart(text=full_response)]
        )
```

## 🔍 Advanced Error Handling

### **1. Circuit Breaker Pattern**

```python
# Circuit breaker for external service failures
from enum import Enum
import time

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"  
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Circuit breaker for external service calls."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = CircuitState.CLOSED
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# Enhanced agent with circuit breaker
class RobustMathAgent(AgentExecutor):
    def __init__(self):
        super().__init__()
        self.llm_circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=300)
        self.external_api_breaker = CircuitBreaker(failure_threshold=5, timeout=60)
    
    async def execute(self, task: Task, context: RequestContext) -> Optional[Message]:
        """Execute with circuit breaker protection."""
        text_content = self._extract_text(task.message)
        
        try:
            # Try LLM processing with circuit breaker
            if self._should_use_llm(text_content):
                result = await self.llm_circuit_breaker.call(
                    self._process_with_llm, text_content
                )
                return self._create_response(result)
        except Exception as e:
            print(f"LLM circuit breaker triggered: {e}")
        
        try:
            # Try external API with circuit breaker
            if self._should_use_external_api(text_content):
                result = await self.external_api_breaker.call(
                    self._process_with_external_api, text_content
                )
                return self._create_response(result)
        except Exception as e:
            print(f"External API circuit breaker triggered: {e}")
        
        # Fall back to deterministic processing
        result = await self._process_deterministic(text_content)
        return self._create_response(f"🔧 Fallback: {result}")
```

### **2. Retry Logic with Backoff**

```python
# Robust retry logic with exponential backoff
import asyncio
import random
from typing import Callable, Any

class RetryManager:
    """Manage retries with exponential backoff."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    async def execute_with_retry(
        self, 
        func: Callable,
        *args,
        exceptions: tuple = (Exception,),
        **kwargs
    ) -> Any:
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    # Calculate delay with exponential backoff and jitter
                    delay = self.base_delay * (2 ** attempt) + random.uniform(0, 1)
                    await asyncio.sleep(delay)
                    print(f"Retry attempt {attempt + 1} after {delay:.2f}s delay")
        
        # All retries failed
        raise last_exception

# Enhanced agent with retry logic
class RetryEnabledMathAgent(AgentExecutor):
    def __init__(self):
        super().__init__()
        self.retry_manager = RetryManager(max_retries=3, base_delay=0.5)
    
    async def execute(self, task: Task, context: RequestContext) -> Optional[Message]:
        """Execute with retry logic."""
        text_content = self._extract_text(task.message)
        
        try:
            # Execute with retry for transient failures
            result = await self.retry_manager.execute_with_retry(
                self._process_with_retries,
                text_content,
                exceptions=(aiohttp.ClientError, asyncio.TimeoutError)
            )
            
            return Message(
                message_id=f"response-{datetime.now().isoformat()}",
                role="agent",
                parts=[TextPart(text=result)]
            )
            
        except Exception as e:
            return self._create_error_response(
                task.message.message_id,
                f"All retry attempts failed: {str(e)}"
            )
```

## 📊 Production Monitoring

### **1. Metrics Collection**

```python
# Prometheus metrics for production monitoring
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

class A2AMetrics:
    """Prometheus metrics for A2A agent."""
    
    def __init__(self):
        # Request metrics
        self.request_count = Counter('a2a_requests_total', 'Total A2A requests', ['agent_name', 'status'])
        self.request_duration = Histogram('a2a_request_duration_seconds', 'Request processing time')
        self.active_requests = Gauge('a2a_active_requests', 'Currently active requests')
        
        # Agent-specific metrics
        self.math_operations = Counter('a2a_math_operations_total', 'Math operations by type', ['operation_type'])
        self.cache_hits = Counter('a2a_cache_hits_total', 'Cache hits vs misses', ['result'])
        self.llm_requests = Counter('a2a_llm_requests_total', 'LLM requests by provider', ['provider', 'status'])
        
        # Error metrics
        self.errors = Counter('a2a_errors_total', 'Errors by type', ['error_type'])
    
    def record_request(self, agent_name: str, status: str):
        """Record request completion."""
        self.request_count.labels(agent_name=agent_name, status=status).inc()
    
    def record_math_operation(self, operation_type: str):
        """Record math operation."""
        self.math_operations.labels(operation_type=operation_type).inc()
    
    def record_cache_result(self, hit: bool):
        """Record cache hit/miss."""
        result = "hit" if hit else "miss"
        self.cache_hits.labels(result=result).inc()

# Instrumented agent
class MonitoredMathAgent(AgentExecutor):
    def __init__(self):
        super().__init__()
        self.metrics = A2AMetrics()
        
        # Start metrics server
        start_http_server(8090)  # Prometheus metrics on port 8090
    
    async def execute(self, task: Task, context: RequestContext) -> Optional[Message]:
        """Execute with metrics collection."""
        start_time = time.time()
        self.metrics.active_requests.inc()
        
        try:
            text_content = self._extract_text(task.message)
            
            # Classify operation type for metrics
            operation_type = self._classify_operation(text_content)
            self.metrics.record_math_operation(operation_type)
            
            # Process request
            result = await self._process_math_request(text_content)
            
            # Record successful request
            self.metrics.record_request("math-agent", "success")
            
            return Message(
                message_id=f"response-{datetime.now().isoformat()}",
                role="agent",
                parts=[TextPart(text=result)]
            )
            
        except Exception as e:
            # Record error
            self.metrics.record_request("math-agent", "error")
            self.metrics.errors.labels(error_type=type(e).__name__).inc()
            
            return self._create_error_response(task.message.message_id, str(e))
        
        finally:
            # Record metrics
            duration = time.time() - start_time
            self.metrics.request_duration.observe(duration)
            self.metrics.active_requests.dec()
```

### **2. Health Checks and Observability**

```python
# Comprehensive health checking
from dataclasses import dataclass
from typing import Dict, List
import psutil
import asyncio

@dataclass
class HealthStatus:
    healthy: bool
    status: str
    details: Dict[str, Any] = None

class HealthChecker:
    """Comprehensive health checking for A2A agent."""
    
    def __init__(self, agent_executor):
        self.agent_executor = agent_executor
    
    async def check_overall_health(self) -> HealthStatus:
        """Check overall system health."""
        checks = [
            ("agent", self._check_agent_health()),
            ("database", self._check_database_health()),
            ("external_services", self._check_external_services()),
            ("system_resources", self._check_system_resources())
        ]
        
        results = {}
        overall_healthy = True
        
        for name, check_coro in checks:
            try:
                result = await asyncio.wait_for(check_coro, timeout=5.0)
                results[name] = result.dict() if hasattr(result, 'dict') else result.__dict__
                if not result.healthy:
                    overall_healthy = False
            except asyncio.TimeoutError:
                results[name] = {"healthy": False, "status": "timeout"}
                overall_healthy = False
            except Exception as e:
                results[name] = {"healthy": False, "status": f"error: {e}"}
                overall_healthy = False
        
        return HealthStatus(
            healthy=overall_healthy,
            status="healthy" if overall_healthy else "degraded",
            details=results
        )
    
    async def _check_agent_health(self) -> HealthStatus:
        """Check agent-specific health."""
        try:
            # Test agent execution with simple request
            test_message = Message(
                message_id="health-check",
                role="user",
                parts=[TextPart(text="2 + 2")]
            )
            
            test_task = Task(message=test_message)
            response = await self.agent_executor.execute(test_task, None)
            
            if response and "4" in str(response.parts[0].text):
                return HealthStatus(healthy=True, status="agent functioning normally")
            else:
                return HealthStatus(healthy=False, status="agent not responding correctly")
        
        except Exception as e:
            return HealthStatus(healthy=False, status=f"agent error: {e}")
    
    async def _check_database_health(self) -> HealthStatus:
        """Check database connectivity."""
        # Placeholder for database health check
        return HealthStatus(healthy=True, status="database not configured")
    
    async def _check_external_services(self) -> HealthStatus:
        """Check external service availability."""
        # Check LLM service availability
        try:
            # Test API endpoints
            external_healthy = True  # Implement actual checks
            return HealthStatus(
                healthy=external_healthy,
                status="external services available"
            )
        except Exception as e:
            return HealthStatus(healthy=False, status=f"external service error: {e}")
    
    async def _check_system_resources(self) -> HealthStatus:
        """Check system resource usage."""
        try:
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Define thresholds
            cpu_threshold = 80
            memory_threshold = 80
            disk_threshold = 90
            
            warnings = []
            if cpu_percent > cpu_threshold:
                warnings.append(f"High CPU usage: {cpu_percent}%")
            if memory.percent > memory_threshold:
                warnings.append(f"High memory usage: {memory.percent}%")
            if disk.percent > disk_threshold:
                warnings.append(f"High disk usage: {disk.percent}%")
            
            healthy = len(warnings) == 0
            status = "resources normal" if healthy else f"resource warnings: {'; '.join(warnings)}"
            
            return HealthStatus(
                healthy=healthy,
                status=status,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent
                }
            )
            
        except Exception as e:
            return HealthStatus(healthy=False, status=f"resource check error: {e}")

# Enhanced FastAPI app with health endpoints
class ProductionA2AApp(A2AFastAPIApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.health_checker = HealthChecker(self.request_handler.agent_executor)
        self.setup_health_endpoints()
    
    def setup_health_endpoints(self):
        @self.app.get("/health")
        async def basic_health():
            """Basic health check."""
            return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
        
        @self.app.get("/health/detailed")
        async def detailed_health():
            """Detailed health check."""
            health_status = await self.health_checker.check_overall_health()
            return health_status.__dict__
        
        @self.app.get("/metrics")
        async def agent_metrics():
            """Agent-specific metrics."""
            return {
                "uptime": time.time() - self.start_time,
                "requests_processed": getattr(self, 'request_count', 0),
                "agent_version": "0.1.0"
            }
```

## 🚀 Production Deployment

### **1. Kubernetes Deployment**

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: a2a-math-agent
  labels:
    app: a2a-math-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: a2a-math-agent
  template:
    metadata:
      labels:
        app: a2a-math-agent
    spec:
      containers:
      - name: a2a-math-agent
        image: a2a-math-agent:v0.1.0
        ports:
        - containerPort: 8002
        env:
        - name: A2A_PORT
          value: "8002"
        - name: LLM_PROVIDER
          value: "openai"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-secrets
              key: openai-api-key
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: database-url
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8002
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/detailed
            port: 8002
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: a2a-math-agent-service
spec:
  selector:
    app: a2a-math-agent
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8002
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: a2a-math-agent-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: math-agent.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: a2a-math-agent-service
            port:
              number: 80
```

### **2. Monitoring and Alerting**

```yaml
# k8s/monitoring.yaml
apiVersion: v1
kind: Service
metadata:
  name: a2a-math-agent-metrics
  labels:
    app: a2a-math-agent
spec:
  selector:
    app: a2a-math-agent
  ports:
  - name: metrics
    port: 8090
    targetPort: 8090
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: a2a-math-agent-monitor
spec:
  selector:
    matchLabels:
      app: a2a-math-agent
  endpoints:
  - port: metrics
    path: /metrics
---
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: a2a-math-agent-alerts
spec:
  groups:
  - name: a2a-math-agent.rules
    rules:
    - alert: A2AMathAgentHighErrorRate
      expr: rate(a2a_requests_total{status="error"}[5m]) > 0.1
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "High error rate in A2A Math Agent"
        description: "Error rate is {{ $value }} requests per second"
    
    - alert: A2AMathAgentHighLatency
      expr: histogram_quantile(0.95, rate(a2a_request_duration_seconds_bucket[5m])) > 5
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "High latency in A2A Math Agent"
        description: "95th percentile latency is {{ $value }} seconds"
```

## 🎯 Key Takeaways

### **🚀 Advanced A2A Features**
1. **Streaming Responses**: Support real-time processing with WebSocket streaming
2. **Multi-Part Messages**: Handle complex messages with different content types
3. **Performance Optimization**: Implement caching, async patterns, and resource pooling
4. **External Integration**: Connect to APIs, databases, and external services
5. **Robust Error Handling**: Circuit breakers, retry logic, and graceful degradation

### **📊 Production Readiness**
- **Monitoring**: Comprehensive metrics with Prometheus integration
- **Health Checks**: Multi-level health checking and observability
- **Deployment**: Kubernetes-ready with proper resource management
- **Alerting**: Proactive alerting for performance and reliability issues
- **Scaling**: Horizontal scaling with load balancing support

### **🛠️ Advanced Patterns**
- **Circuit Breaker**: Protect against cascading failures
- **Retry Logic**: Handle transient failures with exponential backoff
- **Caching**: Improve performance with intelligent response caching
- **Resource Management**: Optimize CPU and memory usage
- **Service Integration**: Connect with external APIs and databases

## 🎓 Congratulations!

You've completed the comprehensive A2A Protocol Tutorial Series! You now have the knowledge and tools to:

- ✅ Understand A2A protocol fundamentals and architecture
- ✅ Configure agent cards and implement discovery mechanisms  
- ✅ Build production-ready A2A agents from scratch
- ✅ Implement advanced features like streaming and multi-part messages
- ✅ Optimize performance and handle complex error scenarios
- ✅ Deploy to production with monitoring and observability

## 🔗 Additional Resources

### **A2A Protocol References**
- **[A2A Protocol Specification](https://a2a-protocol.org/latest/)** - Complete protocol documentation
- **[A2A Python SDK](https://github.com/a2aproject/a2a-python)** - Official Python implementation
- **[Agent Network Sandbox](../../README.md)** - Complete multi-protocol environment

### **Production Examples**
- **[A2A Math Agent](../../agents/a2a-math-agent/)** - Production A2A implementation
- **[Docker Compose Setup](../../docker-compose.yml)** - Multi-agent orchestration
- **[Kubernetes Examples](../../k8s/)** - Production deployment manifests

### **Community and Support**
- **[A2A Community Forum](https://community.a2a-protocol.org/)** - Discussion and support
- **[GitHub Issues](https://github.com/a2aproject/a2a-python/issues)** - Bug reports and feature requests
- **[Documentation](https://docs.a2a-protocol.org/)** - Complete developer documentation

---

*This concludes the Agent Network Sandbox A2A Protocol Tutorial Series. You're now ready to build sophisticated, production-ready A2A agents that can integrate seamlessly into multi-protocol agent ecosystems!*