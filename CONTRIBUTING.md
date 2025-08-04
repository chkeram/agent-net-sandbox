# Contributing to Agent Network Sandbox

Welcome! We're excited that you're interested in contributing to the Agent Network Sandbox. This document provides guidelines and information for contributors.

## 🎯 Project Vision

The Agent Network Sandbox is a comprehensive development environment for building and testing agents across multiple communication protocols. We aim to create a unified platform that enables developers to experiment with different agent frameworks and protocols seamlessly.

## 🤝 Ways to Contribute

### 1. Protocol Implementations
- Add support for new agent protocols (MCP, A2A, custom protocols)
- Improve existing protocol implementations
- Create reference agents for different protocols

### 2. Core Infrastructure
- Enhance the Multi-Protocol Agent Orchestrator
- Improve discovery mechanisms
- Add monitoring and observability features

### 3. Documentation
- Improve setup and usage guides
- Add protocol-specific documentation
- Create tutorials and examples

### 4. Testing & Quality
- Write comprehensive tests
- Improve test coverage
- Add integration tests
- Performance testing and benchmarking

### 5. Bug Reports & Feature Requests
- Report issues with clear reproduction steps
- Suggest new features and improvements
- Participate in discussions and design reviews

## 🚀 Getting Started

### Prerequisites

- **Docker & Docker Compose**: For containerized development
- **Python 3.11+**: For orchestrator and Python agents
- **Git**: For version control
- **curl**: For API testing

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/agent-net-sandbox.git
   cd agent-net-sandbox
   ```

2. **Set Up Development Environment**
   ```bash
   # Start existing services
   docker-compose up -d
   
   # Verify everything is working
   ./scripts/test_all_agents.sh
   ```

3. **Choose Your Development Path**
   
   **For Orchestrator Development:**
   ```bash
   cd agents/orchestrator
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   
   # Run tests
   PYTHONPATH=src python -m pytest tests/ -v
   ```
   
   **For Agent Development:**
   ```bash
   cd agents/acp-hello-world  # or your chosen agent
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Run locally
   export PYTHONPATH=src
   python -m uvicorn hello_agent.app:app --reload
   ```

## 📋 Development Guidelines

### Code Standards

#### Python Code Style
- **Formatter**: Black (line length: 88)
- **Linter**: Ruff with default configuration
- **Type Checking**: MyPy for static type analysis
- **Import Sorting**: Ruff's isort integration

```bash
# Format code
black .

# Lint code
ruff check .

# Type check
mypy src/
```

#### General Principles
- **Type Hints**: All functions must have proper type hints
- **Documentation**: Docstrings for all public functions and classes
- **Error Handling**: Comprehensive error handling with proper logging
- **Security**: Follow security best practices, especially for API keys
- **Testing**: Minimum 75% test coverage for new code

### Commit Message Format

Use conventional commit format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```bash
feat(orchestrator): add support for MCP protocol discovery
fix(acp-agent): handle empty response gracefully
docs(readme): update quick start instructions
test(discovery): add integration tests for agent registration
```

### Branch Naming

- `feat/feature-name` - New features
- `fix/bug-description` - Bug fixes
- `docs/documentation-update` - Documentation improvements
- `refactor/component-name` - Refactoring work

## 🧪 Testing Requirements

### Test Coverage
- **Minimum**: 75% code coverage for new contributions
- **Preferred**: 90%+ coverage for critical components
- **Required**: All new features must include comprehensive tests

### Test Types

1. **Unit Tests**
   ```bash
   # Run unit tests
   python -m pytest tests/test_unit/ -v
   ```

2. **Integration Tests**
   ```bash
   # Run integration tests
   python -m pytest tests/test_integration/ -v
   ```

3. **End-to-End Tests**
   ```bash
   # Test full system
   ./scripts/test_all_agents.sh
   ```

### Test Structure
```
tests/
├── conftest.py              # Shared fixtures
├── fixtures/                # Test fixtures and mocks
├── test_unit/              # Unit tests
├── test_integration/       # Integration tests
└── test_protocols/         # Protocol-specific tests
```

## 🏗️ Adding New Protocols

### Step-by-Step Guide

1. **Research the Protocol**
   - Study the protocol specification
   - Understand message formats and requirements
   - Identify unique features and capabilities

2. **Create Agent Structure**
   ```bash
   mkdir -p agents/{protocol}-{name}
   cd agents/{protocol}-{name}
   
   # Copy template structure
   cp -r ../../templates/agent-template/* .
   ```

3. **Implement Core Functionality**
   - Health check endpoint (`/health`)
   - Protocol-specific endpoints
   - Agent metadata and capabilities
   - Error handling and logging

4. **Add Docker Support**
   ```dockerfile
   # Example Dockerfile structure
   FROM python:3.11-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY src/ ./src/
   
   HEALTHCHECK --interval=30s --timeout=3s \
       CMD curl -f http://localhost:8000/health || exit 1
   
   EXPOSE 8000
   CMD ["python", "-m", "your_agent.app"]
   ```

5. **Update Docker Compose**
   ```yaml
   your-agent-name:
     build:
       context: ./agents/your-protocol-name
       dockerfile: Dockerfile
     ports:
       - "80XX:8000"  # Use next available port
     networks:
       - agent-network
     labels:
       - "agent.protocol=your-protocol"
       - "agent.type=your-type"
       - "agent.capabilities=cap1,cap2"
   ```

6. **Add Orchestrator Support**
   - Update `agents/orchestrator/src/orchestrator/protocols/`
   - Add protocol-specific discovery strategy
   - Update protocol enumeration in models

7. **Create Tests**
   - Unit tests for agent functionality
   - Integration tests with orchestrator
   - Protocol compliance tests

8. **Update Documentation**
   - Agent-specific README
   - Protocol documentation in `docs/protocols/`
   - Update main README with new protocol

## 🔍 Code Review Process

### Pull Request Requirements

1. **Before Submitting**
   - [ ] All tests pass locally
   - [ ] Code follows style guidelines
   - [ ] Documentation is updated
   - [ ] Commit messages follow convention
   - [ ] No security vulnerabilities introduced

2. **PR Description Must Include**
   - Clear description of changes
   - Motivation and context
   - Testing performed
   - Breaking changes (if any)
   - Screenshots for UI changes

3. **Review Process**
   - Automated checks must pass
   - At least one maintainer approval required
   - All conversations must be resolved
   - No merge conflicts

### Review Checklist

**Functionality**
- [ ] Code works as intended
- [ ] Edge cases are handled
- [ ] Error conditions are properly managed
- [ ] Performance implications considered

**Code Quality**
- [ ] Code is readable and well-structured
- [ ] Proper separation of concerns
- [ ] No code duplication
- [ ] Appropriate abstractions

**Testing**
- [ ] Adequate test coverage
- [ ] Tests are meaningful and comprehensive
- [ ] Integration tests included where appropriate

**Documentation**
- [ ] Code is properly documented
- [ ] User-facing documentation updated
- [ ] API documentation current

## 🐛 Bug Reports

### Before Reporting
- Search existing issues for duplicates
- Verify the bug with the latest version
- Check if it's a configuration issue

### Bug Report Template
```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear description of what you expected to happen.

**Environment:**
- OS: [e.g., macOS, Ubuntu 20.04]
- Docker version: [e.g., 20.10.7]
- Python version: [e.g., 3.11.2]
- Agent/Service: [e.g., orchestrator, acp-hello-world]

**Logs**
```
Include relevant log output
```

**Additional context**
Add any other context about the problem here.
```

## 💡 Feature Requests

### Before Requesting
- Check if the feature already exists
- Search existing feature requests
- Consider if it fits the project scope

### Feature Request Template
```markdown
**Is your feature request related to a problem?**
A clear description of what the problem is.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Alternative solutions or features you've considered.

**Additional context**
Add any other context or screenshots about the feature request.

**Implementation ideas**
If you have ideas about how this could be implemented, please share them.
```

## 🚦 Release Process

### Version Numbering
We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped appropriately
- [ ] Tagged release created
- [ ] Docker images published

## 🤔 Questions?

- **General Questions**: Open a [Discussion](https://github.com/your-org/agent-net-sandbox/discussions)
- **Bug Reports**: Open an [Issue](https://github.com/your-org/agent-net-sandbox/issues)
- **Feature Requests**: Open an [Issue](https://github.com/your-org/agent-net-sandbox/issues) with the feature label
- **Security Issues**: See [SECURITY.md](SECURITY.md)

## 📜 Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## 📄 License

By contributing to Agent Network Sandbox, you agree that your contributions will be licensed under the [Apache 2.0 License](LICENSE).

---

Thank you for contributing to Agent Network Sandbox! Your contributions help make multi-protocol agent development more accessible and powerful for everyone. 🤖✨