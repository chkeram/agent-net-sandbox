# {PROTOCOL} {AGENT_NAME} Agent

A {DESCRIPTION} agent implementing the {PROTOCOL} protocol.

## Features

- [ ] Protocol compliance
- [ ] Health checks
- [ ] Error handling
- [ ] Documentation
- [ ] Testing suite

## Quick Start

### Docker

```bash
# Build the agent
docker build -t {AGENT_NAME}-agent .

# Run the agent
docker run -p 8000:8000 {AGENT_NAME}-agent
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the agent
python -m uvicorn app:app --reload
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/` | GET | Agent information |
| Add your endpoints here... |

## Protocol Compliance

Document which protocol features are implemented:

- [ ] Core functionality
- [ ] Authentication
- [ ] Error handling
- [ ] Streaming (if applicable)
- [ ] Configuration
- [ ] Discovery

## Testing

```bash
# Run tests
./test.sh

# Test specific functionality
curl -X GET http://localhost:8000/health
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8000 | Server port |
| `HOST` | 0.0.0.0 | Server host |

## Development

### Adding Features

1. Implement in core logic
2. Add API endpoints
3. Update tests
4. Update documentation

### Protocol Implementation

Follow the {PROTOCOL} specification:
- Link to protocol docs
- Key requirements
- Implementation notes

## Deployment

### Docker Compose

Add to `docker-compose.yml`:

```yaml
  {SERVICE_NAME}:
    build:
      context: ./agents/{AGENT_FOLDER}
      dockerfile: Dockerfile
    ports:
      - "{PORT}:8000"
    networks:
      - agent-network
```

### Health Monitoring

The agent includes health checks:
- Docker health check every 30s
- HTTP endpoint at `/health`
- Status reporting

## Contributing

1. Follow project conventions
2. Add comprehensive tests
3. Update documentation
4. Ensure protocol compliance

## License

Apache 2.0 License - see the LICENSE file for details.