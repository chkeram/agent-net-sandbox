#!/bin/bash

# Script to create a new agent from template
# Usage: ./scripts/create_agent.sh protocol agent-name "Description"

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}🔧 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check arguments
if [ $# -lt 3 ]; then
    echo "Usage: $0 <protocol> <agent-name> <description>"
    echo
    echo "Examples:"
    echo "  $0 mcp hello-world \"Simple MCP hello world agent\""
    echo "  $0 a2a task-manager \"Task management agent using A2A protocol\""
    echo "  $0 custom weather \"Weather information agent with custom protocol\""
    exit 1
fi

PROTOCOL=$1
AGENT_NAME=$2
DESCRIPTION=$3

# Validate inputs
if [[ ! "$PROTOCOL" =~ ^[a-z0-9-]+$ ]]; then
    echo "Error: Protocol must contain only lowercase letters, numbers, and hyphens"
    exit 1
fi

if [[ ! "$AGENT_NAME" =~ ^[a-z0-9-]+$ ]]; then
    echo "Error: Agent name must contain only lowercase letters, numbers, and hyphens"
    exit 1
fi

# Set up variables
AGENT_FOLDER="$PROTOCOL-$AGENT_NAME"
AGENT_PATH="agents/$AGENT_FOLDER"
SERVICE_NAME=$(echo "$AGENT_FOLDER" | tr '-' '_')

print_status "Creating new agent: $AGENT_FOLDER"

# Check if agent already exists
if [ -d "$AGENT_PATH" ]; then
    echo "Error: Agent directory $AGENT_PATH already exists"
    exit 1
fi

# Create agent directory
print_status "Creating directory structure..."
mkdir -p "$AGENT_PATH"

# Copy template files
cp -r templates/agent-template/* "$AGENT_PATH/"

# Replace placeholders in files
print_status "Customizing template files..."

find "$AGENT_PATH" -type f -name "*.md" -o -name "*.py" -o -name "*.sh" -o -name "*.txt" | while read file; do
    sed -i.bak "s/{PROTOCOL}/$PROTOCOL/g" "$file"
    sed -i.bak "s/{AGENT_NAME}/$AGENT_NAME/g" "$file"
    sed -i.bak "s/{DESCRIPTION}/$DESCRIPTION/g" "$file"
    sed -i.bak "s/{AGENT_FOLDER}/$AGENT_FOLDER/g" "$file"
    sed -i.bak "s/{SERVICE_NAME}/$SERVICE_NAME/g" "$file"
    rm "$file.bak"
done

# Make scripts executable
chmod +x "$AGENT_PATH/test.sh"

# Calculate next available port
print_status "Determining port assignment..."
NEXT_PORT=8000
if [ -f "docker-compose.yml" ]; then
    USED_PORTS=$(grep -o '"[0-9]*:8000"' docker-compose.yml | grep -o '[0-9]*' | sort -n)
    for port in $USED_PORTS; do
        if [ $port -ge $NEXT_PORT ]; then
            NEXT_PORT=$((port + 1))
        fi
    done
fi

print_success "Agent created successfully!"
echo
echo "📁 Agent Location: $AGENT_PATH"
echo "🔌 Protocol: $PROTOCOL"
echo "🤖 Agent Name: $AGENT_NAME"
echo "📝 Description: $DESCRIPTION"
echo "🚪 Suggested Port: $NEXT_PORT"
echo

print_warning "Next Steps:"
echo "1. Customize the agent implementation in $AGENT_PATH/src/"
echo "2. Update requirements.txt with protocol-specific dependencies"
echo "3. Add your service to docker-compose.yml:"
echo
echo "  $SERVICE_NAME:"
echo "    build:"
echo "      context: ./$AGENT_PATH"
echo "      dockerfile: Dockerfile"
echo "    ports:"
echo "      - \"$NEXT_PORT:8000\""
echo "    networks:"
echo "      - agent-network"
echo "    labels:"
echo "      - \"agent.protocol=$PROTOCOL\""
echo "      - \"agent.type=$AGENT_NAME\""
echo
echo "4. Add proxy configuration to scripts/nginx.conf:"
echo "   location /agents/$AGENT_FOLDER {"
echo "       proxy_pass http://$SERVICE_NAME:8000;"
echo "       # ... proxy headers"
echo "   }"
echo
echo "5. Create test script: scripts/agents/test_$PROTOCOL.sh"
echo "6. Update the agent directory HTML page"
echo "7. Test your agent:"
echo "   cd $AGENT_PATH && ./test.sh"
echo

print_success "Happy agent building! 🚀"