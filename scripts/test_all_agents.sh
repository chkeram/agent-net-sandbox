#!/bin/bash

# Master test script for all agents in the multi-protocol sandbox
# Tests all available agents and provides comprehensive reporting

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "INFO")  echo -e "${BLUE}ℹ️  $message${NC}" ;;
        "PASS")  echo -e "${GREEN}✅ $message${NC}" ;;
        "FAIL")  echo -e "${RED}❌ $message${NC}" ;;
        "WARN")  echo -e "${YELLOW}⚠️  $message${NC}" ;;
        "HEADER") echo -e "${PURPLE}🚀 $message${NC}" ;;
    esac
}

# Function to check if agent is running
check_agent() {
    local name=$1
    local url=$2
    local health_endpoint=${3:-/health}
    
    print_status "INFO" "Checking $name at $url$health_endpoint"
    
    if curl -s --max-time 5 "$url$health_endpoint" >/dev/null 2>&1; then
        print_status "PASS" "$name is running"
        return 0
    else
        print_status "FAIL" "$name is not responding"
        return 1
    fi
}

# Function to run agent-specific tests
test_agent() {
    local protocol=$1
    local name=$2
    local url=$3
    local test_script="./scripts/agents/test_${protocol}.sh"
    
    print_status "HEADER" "Testing $name ($protocol protocol)"
    echo "============================================"
    
    if [ -f "$test_script" ]; then
        if AGENT_URL="$url" "$test_script"; then
            print_status "PASS" "$name tests completed successfully"
            return 0
        else
            print_status "FAIL" "$name tests failed"
            return 1
        fi
    else
        print_status "WARN" "No test script found for $protocol protocol ($test_script)"
        return 1
    fi
}

# Main test execution
main() {
    echo "🧪 Multi-Protocol Agent Sandbox Test Suite"
    echo "============================================="
    echo "Testing all available agents..."
    echo

    local total_agents=0
    local passing_agents=0
    local agents_tested=()

    # Test ACP Hello World Agent
    local acp_url="http://localhost:8000"
    ((total_agents++))
    if check_agent "ACP Hello World Agent" "$acp_url" && test_agent "acp" "ACP Hello World Agent" "$acp_url"; then
        ((passing_agents++))
        agents_tested+=("✅ ACP Hello World Agent")
    else
        agents_tested+=("❌ ACP Hello World Agent")
    fi
    echo

    # Test MCP Agent (if available)
    local mcp_url="http://localhost:8001"
    if check_agent "MCP Agent" "$mcp_url" "/health" 2>/dev/null; then
        ((total_agents++))
        if test_agent "mcp" "MCP Agent" "$mcp_url"; then
            ((passing_agents++))
            agents_tested+=("✅ MCP Agent")
        else
            agents_tested+=("❌ MCP Agent")
        fi
        echo
    else
        print_status "INFO" "MCP Agent not running (expected if not implemented yet)"
    fi

    # Test A2A Agent (if available)
    local a2a_url="http://localhost:8002"
    if check_agent "A2A Agent" "$a2a_url" "/health" 2>/dev/null; then
        ((total_agents++))
        if test_agent "a2a" "A2A Agent" "$a2a_url"; then
            ((passing_agents++))
            agents_tested+=("✅ A2A Agent")
        else
            agents_tested+=("❌ A2A Agent")
        fi
        echo
    else
        print_status "INFO" "A2A Agent not running (expected if not implemented yet)"
    fi

    # Test Custom Protocol Agents (port 8003+)
    for port in 8003 8004 8005; do
        local custom_url="http://localhost:$port"
        if check_agent "Custom Agent (port $port)" "$custom_url" "/health" 2>/dev/null; then
            ((total_agents++))
            if test_agent "custom" "Custom Agent (port $port)" "$custom_url"; then
                ((passing_agents++))
                agents_tested+=("✅ Custom Agent (port $port)")
            else
                agents_tested+=("❌ Custom Agent (port $port)")
            fi
            echo
        fi
    done

    # Test Agent Directory
    local directory_url="http://localhost:8080"
    if check_agent "Agent Directory" "$directory_url" "/" 2>/dev/null; then
        print_status "PASS" "Agent Directory is accessible"
    else
        print_status "WARN" "Agent Directory is not accessible"
    fi

    # Summary Report
    echo "============================================="
    print_status "HEADER" "Test Summary Report"
    echo "============================================="
    
    print_status "INFO" "Agents tested: $total_agents"
    print_status "INFO" "Agents passing: $passing_agents"
    
    echo
    print_status "INFO" "Agent Status:"
    for agent_status in "${agents_tested[@]}"; do
        echo "  $agent_status"
    done
    
    echo
    print_status "INFO" "Service URLs:"
    echo "  🤖 ACP Hello World: http://localhost:8000"
    echo "  🔌 MCP Agent: http://localhost:8001 (if running)"
    echo "  🤝 A2A Agent: http://localhost:8002 (if running)"
    echo "  📁 Agent Directory: http://localhost:8080"
    
    echo
    if [ $passing_agents -eq $total_agents ] && [ $total_agents -gt 0 ]; then
        print_status "PASS" "All agents are working correctly! 🎉"
        exit 0
    elif [ $total_agents -eq 0 ]; then
        print_status "WARN" "No agents are currently running."
        print_status "INFO" "Start agents with: docker-compose up -d"
        exit 1
    else
        print_status "FAIL" "Some agents have issues."
        print_status "INFO" "Check individual agent logs: docker-compose logs [service-name]"
        exit 1
    fi
}

# Show usage if help requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0"
    echo
    echo "Tests all available agents in the multi-protocol sandbox."
    echo
    echo "Prerequisites:"
    echo "  - Agents should be running (docker-compose up -d)"
    echo "  - curl should be available"
    echo "  - Individual agent test scripts in scripts/agents/"
    echo
    echo "Examples:"
    echo "  $0                    # Test all agents"
    echo "  $0 --help            # Show this help"
    exit 0
fi

# Change to project root directory
cd "$(dirname "$0")/.."

# Run main test function
main