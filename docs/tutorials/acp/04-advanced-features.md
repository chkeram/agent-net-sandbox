# Part 4: Advanced Features

## 🎯 Learning Objectives

By the end of this tutorial, you will:
- Implement streaming responses for real-time data
- Master advanced configuration management patterns
- Integrate your agent with the Multi-Protocol Orchestrator
- Optimize performance and implement caching
- Deploy to production with best practices
- Handle errors gracefully at scale

## 📚 Prerequisites

- Completed Parts 1-3 of this series
- Working ACP agent from Part 3
- Understanding of async programming in Python
- Docker and Docker Compose knowledge

## 🌊 Streaming Responses

Streaming allows agents to send real-time updates during long-running operations. Let's examine our implementation:

### Implementation from Hello World Agent

```python
# From agents/acp-hello-world/src/hello_agent/app.py

@app.post("/invoke/stream")
async def invoke_stream(request: InvokeRequest):
    """
    Optional: Streaming invocation endpoint.
    Streams responses for real-time updates.
    """
    async def generate():
        # Initial acknowledgment
        yield f"data: {json.dumps({'status': 'started', 'timestamp': time.time()})}\n\n"
        
        # Process in chunks
        for i in range(5):
            await asyncio.sleep(0.5)  # Simulate processing
            
            chunk = {
                "status": "processing",
                "progress": (i + 1) * 20,
                "message": f"Processing step {i + 1} of 5"
            }
            yield f"data: {json.dumps(chunk)}\n\n"
        
        # Final result
        result = agent.execute(request.input, request.config_id)
        yield f"data: {json.dumps({'status': 'complete', 'result': result})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable Nginx buffering
        }
    )
```

### Advanced Streaming Pattern

Here's a more sophisticated streaming implementation with error handling:

```python
import asyncio
from typing import AsyncIterator
import traceback

class StreamingAgent:
    """Advanced streaming capabilities for ACP agents."""
    
    async def process_with_updates(
        self, 
        input_data: Dict[str, Any],
        update_interval: float = 1.0
    ) -> AsyncIterator[Dict[str, Any]]:
        """Process input with periodic status updates."""
        
        try:
            # Start processing
            yield {"event": "start", "timestamp": time.time()}
            
            # Validate input
            yield {"event": "validating", "message": "Validating input data"}
            if not self.validate_input(input_data):
                yield {"event": "error", "error": "Invalid input data"}
                return
            
            # Fetch external data (simulated)
            yield {"event": "fetching", "message": "Fetching external data"}
            await asyncio.sleep(update_interval)
            
            # Process data
            total_steps = 10
            for step in range(total_steps):
                progress = ((step + 1) / total_steps) * 100
                yield {
                    "event": "processing",
                    "step": step + 1,
                    "total": total_steps,
                    "progress": progress,
                    "message": f"Processing step {step + 1}/{total_steps}"
                }
                
                # Simulate work
                await asyncio.sleep(update_interval)
                
                # Check for cancellation
                if hasattr(asyncio.current_task(), 'cancelled') and asyncio.current_task().cancelled():
                    yield {"event": "cancelled", "message": "Processing cancelled"}
                    return
            
            # Generate final result
            result = await self.generate_result(input_data)
            yield {
                "event": "complete",
                "result": result,
                "timestamp": time.time()
            }
            
        except Exception as e:
            yield {
                "event": "error",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

# Using the streaming agent
@app.post("/invoke/advanced-stream")
async def advanced_stream(request: InvokeRequest):
    """Advanced streaming with granular updates."""
    
    async def stream_generator():
        async for update in agent.process_with_updates(request.input):
            yield f"data: {json.dumps(update)}\n\n"
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream"
    )
```

### Client-Side Streaming Consumption

```python
# Example client code to consume streaming responses
import httpx
import json

async def consume_stream():
    """Consume streaming responses from ACP agent."""
    
    async with httpx.AsyncClient() as client:
        async with client.stream(
            'POST',
            'http://localhost:8000/invoke/stream',
            json={"input": {"city": "London"}},
            timeout=None
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    
                    if data.get('event') == 'processing':
                        print(f"Progress: {data['progress']:.1f}%")
                    elif data.get('event') == 'complete':
                        print(f"Result: {data['result']}")
                    elif data.get('event') == 'error':
                        print(f"Error: {data['error']}")
```

## ⚙️ Advanced Configuration Management

### Dynamic Configuration Updates

```python
class ConfigurableAgent:
    """Agent with advanced configuration management."""
    
    def __init__(self):
        self.config_store = {}
        self.config_versions = {}
        self.active_configs = {}
        
    def store_config_versioned(
        self, 
        config_data: Dict[str, Any],
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Store configuration with versioning support."""
        
        # Validate configuration
        config = AgentConfig(**config_data)
        
        # Generate IDs
        config_id = f"cfg_{uuid.uuid4().hex[:8]}"
        version = version or f"v{int(time.time())}"
        
        # Store with version tracking
        if config_id not in self.config_versions:
            self.config_versions[config_id] = []
        
        self.config_versions[config_id].append({
            "version": version,
            "config": config.model_dump(),
            "created_at": datetime.utcnow().isoformat(),
            "active": True
        })
        
        # Deactivate previous versions
        for v in self.config_versions[config_id][:-1]:
            v["active"] = False
        
        self.config_store[config_id] = config
        
        return {
            "config_id": config_id,
            "version": version,
            "status": "created"
        }
    
    def rollback_config(self, config_id: str, version: str) -> bool:
        """Rollback to a previous configuration version."""
        
        if config_id not in self.config_versions:
            return False
        
        for v in self.config_versions[config_id]:
            if v["version"] == version:
                # Reactivate this version
                v["active"] = True
                self.config_store[config_id] = AgentConfig(**v["config"])
                
                # Deactivate others
                for other in self.config_versions[config_id]:
                    if other["version"] != version:
                        other["active"] = False
                
                return True
        
        return False
    
    def get_config_history(self, config_id: str) -> List[Dict[str, Any]]:
        """Get configuration history for audit."""
        return self.config_versions.get(config_id, [])
```

### Environment-Based Configuration

```python
import os
from pydantic_settings import BaseSettings

class AgentSettings(BaseSettings):
    """Environment-based agent settings."""
    
    # Agent identity
    agent_id: str = "acp-agent"
    agent_name: str = "ACP Agent"
    version: str = "0.1.0"
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # Performance settings
    max_workers: int = 4
    request_timeout: int = 30
    cache_ttl: int = 300
    
    # Feature flags
    enable_streaming: bool = True
    enable_caching: bool = True
    enable_metrics: bool = True
    
    # External services
    orchestrator_url: Optional[str] = None
    discovery_url: Optional[str] = None
    
    class Config:
        env_prefix = "ACP_"
        env_file = ".env"

# Usage
settings = AgentSettings()

# Access in code
app = FastAPI(
    title=settings.agent_name,
    version=settings.version,
    debug=settings.debug
)
```

## 🔄 Orchestrator Integration

### Registering with the Orchestrator

```python
import httpx
from typing import Optional

class OrchestrationClient:
    """Client for integrating with Multi-Protocol Orchestrator."""
    
    def __init__(self, orchestrator_url: str, agent_info: Dict[str, Any]):
        self.orchestrator_url = orchestrator_url
        self.agent_info = agent_info
        self.client = httpx.AsyncClient()
        self.registration_id = None
        
    async def register(self) -> bool:
        """Register agent with orchestrator."""
        
        try:
            # Prepare registration data
            registration_data = {
                "agent_id": self.agent_info["agent_id"],
                "name": self.agent_info["name"],
                "protocol": "acp",
                "endpoint": self.agent_info["base_url"],
                "capabilities": self.agent_info["capabilities"],
                "metadata": {
                    "version": self.agent_info["version"],
                    "tags": self.agent_info.get("tags", []),
                    "discovery_method": "self_registration"
                }
            }
            
            # Send registration
            response = await self.client.post(
                f"{self.orchestrator_url}/agents/register",
                json=registration_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.registration_id = data.get("registration_id")
                return True
                
        except Exception as e:
            print(f"Registration failed: {e}")
            
        return False
    
    async def send_heartbeat(self) -> bool:
        """Send heartbeat to maintain registration."""
        
        if not self.registration_id:
            return False
        
        try:
            response = await self.client.post(
                f"{self.orchestrator_url}/agents/{self.registration_id}/heartbeat",
                json={"status": "healthy", "timestamp": time.time()}
            )
            return response.status_code == 200
            
        except Exception:
            return False
    
    async def update_capabilities(self, capabilities: List[Dict[str, Any]]) -> bool:
        """Update agent capabilities in orchestrator."""
        
        if not self.registration_id:
            return False
        
        try:
            response = await self.client.put(
                f"{self.orchestrator_url}/agents/{self.registration_id}/capabilities",
                json={"capabilities": capabilities}
            )
            return response.status_code == 200
            
        except Exception:
            return False

# Integration in FastAPI startup
@app.on_event("startup")
async def startup_event():
    """Register with orchestrator on startup."""
    
    if settings.orchestrator_url:
        orchestration = OrchestrationClient(
            settings.orchestrator_url,
            agent.get_info()
        )
        
        if await orchestration.register():
            print(f"Registered with orchestrator: {orchestration.registration_id}")
            
            # Start heartbeat task
            asyncio.create_task(heartbeat_loop(orchestration))
        else:
            print("Failed to register with orchestrator")

async def heartbeat_loop(orchestration: OrchestrationClient):
    """Maintain registration with periodic heartbeats."""
    
    while True:
        await asyncio.sleep(30)  # Every 30 seconds
        
        if not await orchestration.send_heartbeat():
            # Try to re-register
            await orchestration.register()
```

## 🚀 Performance Optimization

### Caching Implementation

```python
from functools import lru_cache
from aiocache import Cache
from aiocache.serializers import JsonSerializer

class CachedAgent:
    """Agent with caching capabilities."""
    
    def __init__(self):
        self.cache = Cache(Cache.MEMORY)
        self.cache.serializer = JsonSerializer()
        
    @lru_cache(maxsize=128)
    def get_static_capabilities(self) -> Dict[str, Any]:
        """Cache static capabilities."""
        return self._load_capabilities()
    
    async def get_cached_result(
        self, 
        input_hash: str,
        ttl: int = 300
    ) -> Optional[Dict[str, Any]]:
        """Get cached result if available."""
        
        key = f"result:{input_hash}"
        return await self.cache.get(key)
    
    async def cache_result(
        self,
        input_hash: str,
        result: Dict[str, Any],
        ttl: int = 300
    ):
        """Cache computation result."""
        
        key = f"result:{input_hash}"
        await self.cache.set(key, result, ttl=ttl)
    
    async def execute_with_cache(
        self,
        input_data: Dict[str, Any],
        config_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute with caching support."""
        
        # Generate cache key
        import hashlib
        input_str = json.dumps(input_data, sort_keys=True)
        input_hash = hashlib.md5(input_str.encode()).hexdigest()
        
        # Check cache
        cached = await self.get_cached_result(input_hash)
        if cached:
            cached["_from_cache"] = True
            return cached
        
        # Execute normally
        result = self.execute(input_data, config_id)
        
        # Cache result
        await self.cache_result(input_hash, result)
        
        return result
```

### Connection Pooling

```python
import httpx
from contextlib import asynccontextmanager

class ConnectionPool:
    """Manage connection pools for external services."""
    
    def __init__(self):
        self.clients = {}
        
    @asynccontextmanager
    async def get_client(self, service: str) -> httpx.AsyncClient:
        """Get or create client for service."""
        
        if service not in self.clients:
            self.clients[service] = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                limits=httpx.Limits(
                    max_keepalive_connections=5,
                    max_connections=10
                )
            )
        
        yield self.clients[service]
    
    async def close_all(self):
        """Close all client connections."""
        
        for client in self.clients.values():
            await client.aclose()
        
        self.clients.clear()

# Global connection pool
pool = ConnectionPool()

# Usage in endpoint
@app.post("/invoke-external")
async def invoke_with_external(request: InvokeRequest):
    """Invoke agent with external service calls."""
    
    async with pool.get_client("weather-api") as client:
        response = await client.get(
            f"https://api.weather.com/v1/location/{request.input['city']}"
        )
        weather_data = response.json()
    
    # Process with weather data
    result = agent.process_with_weather(request.input, weather_data)
    return InvokeResponse(output=result)

# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    await pool.close_all()
```

## 🛡️ Production Error Handling

### Comprehensive Error Management

```python
from enum import Enum
from typing import Optional
import logging

class ErrorCode(Enum):
    """Standardized error codes."""
    INVALID_INPUT = "INVALID_INPUT"
    CONFIG_NOT_FOUND = "CONFIG_NOT_FOUND"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    TIMEOUT = "TIMEOUT"

class ACPError(Exception):
    """Base ACP error class."""
    
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)
    
    def to_response(self) -> Dict[str, Any]:
        """Convert to API response."""
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "details": self.details,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

# Error handler middleware
@app.exception_handler(ACPError)
async def acp_error_handler(request, exc: ACPError):
    """Handle ACP-specific errors."""
    
    # Log error
    logging.error(
        f"ACP Error: {exc.code.value}",
        extra={
            "code": exc.code.value,
            "message": exc.message,
            "details": exc.details,
            "path": request.url.path
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_response()
    )

# Usage in agent
class RobustAgent:
    """Agent with robust error handling."""
    
    async def execute_safely(
        self,
        input_data: Dict[str, Any],
        config_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute with comprehensive error handling."""
        
        # Validate input
        try:
            validated_input = WeatherInput(**input_data)
        except ValidationError as e:
            raise ACPError(
                code=ErrorCode.INVALID_INPUT,
                message="Input validation failed",
                details={"validation_errors": e.errors()},
                status_code=400
            )
        
        # Check configuration
        if config_id and config_id not in self.config_store:
            raise ACPError(
                code=ErrorCode.CONFIG_NOT_FOUND,
                message=f"Configuration {config_id} not found",
                status_code=404
            )
        
        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                self.execute(input_data, config_id),
                timeout=30.0
            )
            return result
            
        except asyncio.TimeoutError:
            raise ACPError(
                code=ErrorCode.TIMEOUT,
                message="Execution timeout",
                details={"timeout_seconds": 30},
                status_code=504
            )
        except Exception as e:
            raise ACPError(
                code=ErrorCode.EXECUTION_ERROR,
                message="Execution failed",
                details={"error": str(e)},
                status_code=500
            )
```

## 📊 Metrics and Monitoring

### Prometheus Metrics Integration

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
import time

# Define metrics
request_count = Counter(
    'acp_agent_requests_total',
    'Total number of requests',
    ['endpoint', 'status']
)

request_duration = Histogram(
    'acp_agent_request_duration_seconds',
    'Request duration in seconds',
    ['endpoint']
)

active_configs = Gauge(
    'acp_agent_active_configs',
    'Number of active configurations'
)

# Metrics middleware
@app.middleware("http")
async def metrics_middleware(request, call_next):
    """Track metrics for all requests."""
    
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Record metrics
    duration = time.time() - start_time
    request_count.labels(
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    request_duration.labels(
        endpoint=request.url.path
    ).observe(duration)
    
    return response

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# Update gauge metrics
@app.post("/config")
async def create_config_with_metrics(request: ConfigRequest):
    """Create config and update metrics."""
    
    result = agent.store_config(request.config)
    active_configs.set(len(agent.config_store))
    return ConfigResponse(**result)
```

### Structured Logging

```python
import structlog
from pythonjsonlogger import jsonlogger

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Use in agent
class LoggingAgent:
    """Agent with structured logging."""
    
    def __init__(self):
        self.logger = structlog.get_logger().bind(
            agent_id=self.agent_id,
            version=self.version
        )
    
    async def execute_with_logging(
        self,
        input_data: Dict[str, Any],
        config_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute with detailed logging."""
        
        # Create request context
        request_id = str(uuid.uuid4())
        log = self.logger.bind(
            request_id=request_id,
            config_id=config_id
        )
        
        log.info("Starting execution", input=input_data)
        
        try:
            # Validate
            log.debug("Validating input")
            validated = self.validate_input(input_data)
            
            # Execute
            log.info("Executing agent logic")
            result = self.execute(input_data, config_id)
            
            log.info("Execution complete", result_size=len(str(result)))
            return result
            
        except Exception as e:
            log.error("Execution failed", error=str(e), exc_info=True)
            raise
```

## 🐳 Production Deployment

### Docker Compose Integration

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  acp-agent:
    build:
      context: ./agents/acp-weather-advisor
      dockerfile: Dockerfile
    image: acp-weather-advisor:latest
    container_name: acp-weather-advisor
    ports:
      - "8000:8000"
    environment:
      - ACP_AGENT_ID=weather-advisor
      - ACP_HOST=0.0.0.0
      - ACP_PORT=8000
      - ACP_DEBUG=false
      - ACP_ENABLE_METRICS=true
      - ACP_ORCHESTRATOR_URL=http://orchestrator:8004
      - ACP_CACHE_TTL=300
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    networks:
      - agent-network
    labels:
      - "agent.protocol=acp"
      - "agent.type=weather-advisor"
      - "agent.version=0.1.0"
      - "prometheus.io/scrape=true"
      - "prometheus.io/port=8000"
      - "prometheus.io/path=/metrics"
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M

networks:
  agent-network:
    external: true
```

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: acp-weather-advisor
  labels:
    app: acp-weather-advisor
    protocol: acp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: acp-weather-advisor
  template:
    metadata:
      labels:
        app: acp-weather-advisor
        protocol: acp
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: agent
        image: acp-weather-advisor:latest
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: ACP_AGENT_ID
          value: "weather-advisor"
        - name: ACP_ORCHESTRATOR_URL
          value: "http://orchestrator:8004"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        resources:
          limits:
            cpu: 500m
            memory: 512Mi
          requests:
            cpu: 250m
            memory: 256Mi
---
apiVersion: v1
kind: Service
metadata:
  name: acp-weather-advisor
spec:
  selector:
    app: acp-weather-advisor
  ports:
  - port: 8000
    targetPort: 8000
    name: http
  type: ClusterIP
```

## 🔐 Security Best Practices

### API Key Authentication

```python
from fastapi.security import APIKeyHeader
from fastapi import Security, HTTPException, status

# API Key configuration
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Store API keys securely (use secrets management in production)
VALID_API_KEYS = {
    "sk_live_abc123": "production",
    "sk_test_xyz789": "development"
}

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key for protected endpoints."""
    
    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key"
        )
    
    return VALID_API_KEYS[api_key]

# Protected endpoint
@app.post("/invoke", dependencies=[Security(verify_api_key)])
async def invoke_protected(request: InvokeRequest):
    """Protected invocation endpoint."""
    return await invoke_agent(request)

# Update auth endpoint to reflect authentication
@app.get("/auth")
async def get_auth_info():
    return AuthInfo(
        type="api_key",
        description="API key required in X-API-Key header",
        required=True
    )
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Create limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"]
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply rate limiting
@app.post("/invoke")
@limiter.limit("10 per minute")
async def invoke_rate_limited(request: Request, invoke_request: InvokeRequest):
    """Rate-limited invocation endpoint."""
    return await invoke_agent(invoke_request)
```

## 🎯 Production Checklist

Before deploying to production:

- [ ] **Security**
  - [ ] Authentication implemented
  - [ ] Rate limiting configured
  - [ ] CORS properly configured
  - [ ] Secrets in environment variables
  - [ ] HTTPS enabled

- [ ] **Performance**
  - [ ] Caching implemented
  - [ ] Connection pooling configured
  - [ ] Async operations optimized
  - [ ] Resource limits set

- [ ] **Monitoring**
  - [ ] Metrics endpoint exposed
  - [ ] Structured logging configured
  - [ ] Health checks implemented
  - [ ] Alerts configured

- [ ] **Reliability**
  - [ ] Error handling comprehensive
  - [ ] Timeouts configured
  - [ ] Retry logic implemented
  - [ ] Graceful shutdown handling

- [ ] **Deployment**
  - [ ] Docker image optimized
  - [ ] Environment configs separated
  - [ ] Scaling strategy defined
  - [ ] Backup/recovery plan

## 🎓 Advanced Exercises

1. **Implement OAuth2**: Add OAuth2 authentication flow
2. **Add GraphQL**: Create GraphQL endpoint alongside REST
3. **Implement WebSockets**: Add real-time bidirectional communication
4. **Create Admin API**: Build management endpoints for the agent
5. **Add Tracing**: Implement distributed tracing with OpenTelemetry

## 📚 Additional Resources

- [FastAPI Advanced Guide](https://fastapi.tiangolo.com/advanced/)
- [Prometheus Python Client](https://github.com/prometheus/client_python)
- [Structlog Documentation](https://www.structlog.org/)
- [Docker Production Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Kubernetes Patterns](https://k8spatterns.io/)

## 🎉 Conclusion

Congratulations! You've completed the ACP Protocol tutorial series. You now have:

1. **Deep understanding** of ACP protocol fundamentals
2. **Configuration expertise** with manifests and descriptors
3. **Practical experience** building a complete agent
4. **Advanced knowledge** of streaming, caching, and production deployment

### What You've Learned

- ✅ All five required ACP endpoints
- ✅ Configuration and discovery patterns
- ✅ Building agents from scratch
- ✅ Streaming for real-time updates
- ✅ Performance optimization techniques
- ✅ Production deployment strategies
- ✅ Security best practices
- ✅ Monitoring and observability

### Next Steps

1. **Build your own agent** with unique capabilities
2. **Contribute** to the Agent Network Sandbox
3. **Explore** other protocols (A2A, MCP)
4. **Share** your implementations with the community

Thank you for completing this tutorial series! You're now equipped to build production-ready ACP agents that can integrate seamlessly with the multi-protocol ecosystem.

---

*This tutorial series is part of the Agent Network Sandbox educational initiative. All code follows official ACP specifications and production best practices.*

**Happy agent building! 🤖✨**