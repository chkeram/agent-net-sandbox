#!/bin/bash

# API Testing Script for Hello World Agent
# Tests all ACP endpoints and functionality

set -e

# Configuration
AGENT_URL="${AGENT_URL:-http://localhost:8000}"
TIMEOUT=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
    esac
}

# Function to test HTTP endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_status=${4:-200}
    local description=$5
    
    print_status "INFO" "Testing: $description"
    
    if [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
                   -H "Content-Type: application/json" \
                   -d "$data" \
                   --max-time $TIMEOUT \
                   "$AGENT_URL$endpoint" 2>/dev/null)
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
                   --max-time $TIMEOUT \
                   "$AGENT_URL$endpoint" 2>/dev/null)
    fi
    
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$status_code" -eq "$expected_status" ]; then
        print_status "PASS" "$description (HTTP $status_code)"
        if [ -n "$body" ] && command -v jq >/dev/null 2>&1; then
            echo "$body" | jq . 2>/dev/null || echo "$body"
        else
            echo "$body"
        fi
        echo
        return 0
    else
        print_status "FAIL" "$description (Expected HTTP $expected_status, got HTTP $status_code)"
        echo "$body"
        echo
        return 1
    fi
}

# Function to wait for agent to be ready
wait_for_agent() {
    print_status "INFO" "Waiting for agent at $AGENT_URL to be ready..."
    
    for i in {1..30}; do
        if curl -s --max-time 5 "$AGENT_URL/health" >/dev/null 2>&1; then
            print_status "PASS" "Agent is ready!"
            return 0
        fi
        echo -n "."
        sleep 2
    done
    
    print_status "FAIL" "Agent did not become ready within 60 seconds"
    return 1
}

# Main test execution
main() {
    echo "🧪 AGNTCY Hello World Agent API Test Suite"
    echo "=========================================="
    echo "Agent URL: $AGENT_URL"
    echo "Timeout: $TIMEOUT seconds"
    echo

    # Wait for agent to be ready
    wait_for_agent || exit 1
    echo

    local tests_passed=0
    local tests_total=0

    # Test 1: Health Check
    ((tests_total++))
    if test_endpoint "GET" "/health" "" 200 "Health Check"; then
        ((tests_passed++))
    fi

    # Test 2: Root Information
    ((tests_total++))
    if test_endpoint "GET" "/" "" 200 "Root Information"; then
        ((tests_passed++))
    fi

    # Test 3: Authentication Info (ACP Required)
    ((tests_total++))
    if test_endpoint "GET" "/auth" "" 200 "Authentication Information"; then
        ((tests_passed++))
    fi

    # Test 4: Schema Definitions (ACP Required)
    ((tests_total++))
    if test_endpoint "GET" "/schema" "" 200 "Schema Definitions"; then
        ((tests_passed++))
    fi

    # Test 5: Agent Capabilities (ACP Required)
    ((tests_total++))
    if test_endpoint "GET" "/capabilities" "" 200 "Agent Capabilities"; then
        ((tests_passed++))
    fi

    # Test 6: Simple Hello (Direct endpoint)
    ((tests_total++))
    hello_input='{"name": "Test User", "language": "en"}'
    if test_endpoint "POST" "/hello" "$hello_input" 200 "Simple Hello Request"; then
        ((tests_passed++))
    fi

    # Test 7: ACP Invoke (Protocol compliant)
    ((tests_total++))
    invoke_request='{"input": {"name": "AGNTCY", "language": "en"}}'
    if test_endpoint "POST" "/invoke" "$invoke_request" 200 "ACP Invoke Request"; then
        ((tests_passed++))
    fi

    # Test 8: Configuration Creation (ACP Required)
    ((tests_total++))
    config_request='{"config": {"agent_name": "Test Agent", "default_language": "es"}}'
    if test_endpoint "POST" "/config" "$config_request" 200 "Configuration Creation"; then
        ((tests_passed++))
    fi

    # Test 9: Multi-language Support
    ((tests_total++))
    spanish_request='{"input": {"name": "Mundo", "language": "es"}}'
    if test_endpoint "POST" "/invoke" "$spanish_request" 200 "Spanish Language Support"; then
        ((tests_passed++))
    fi

    # Test 10: French Language Support
    ((tests_total++))
    french_request='{"input": {"name": "Monde", "language": "fr"}}'
    if test_endpoint "POST" "/invoke" "$french_request" 200 "French Language Support"; then
        ((tests_passed++))
    fi

    # Test 11: Custom Message Support
    ((tests_total++))
    custom_request='{"input": {"name": "Developer", "message": "Welcome to AGNTCY"}}'
    if test_endpoint "POST" "/invoke" "$custom_request" 200 "Custom Message Support"; then
        ((tests_passed++))
    fi

    # Test 12: Error Handling (Invalid endpoint)
    ((tests_total++))
    if test_endpoint "GET" "/nonexistent" "" 404 "Error Handling - 404"; then
        ((tests_passed++))
    fi

    # Summary
    echo "=========================================="
    echo "📊 Test Results Summary"
    echo "=========================================="
    print_status "INFO" "Tests passed: $tests_passed/$tests_total"
    
    if [ $tests_passed -eq $tests_total ]; then
        print_status "PASS" "All tests passed! 🎉"
        exit 0
    else
        print_status "FAIL" "Some tests failed."
        exit 1
    fi
}

# Show usage if help requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [AGENT_URL]"
    echo
    echo "Environment variables:"
    echo "  AGENT_URL    Agent base URL (default: http://localhost:8000)"
    echo
    echo "Examples:"
    echo "  $0                              # Test localhost:8000"
    echo "  $0 http://localhost:8080        # Test specific URL"
    echo "  AGENT_URL=http://remote:8000 $0 # Test remote agent"
    exit 0
fi

# Override AGENT_URL if provided as argument
if [ -n "$1" ]; then
    AGENT_URL="$1"
fi

# Run main test function
main