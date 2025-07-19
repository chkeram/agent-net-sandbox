#!/bin/bash

# Template test script for agents
# Customize this script for your specific protocol and endpoints

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
    echo "🧪 {PROTOCOL} {AGENT_NAME} Agent Test Suite"
    echo "=============================================="
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

    # Test 3: Agent Info
    ((tests_total++))
    if test_endpoint "GET" "/info" "" 200 "Agent Information"; then
        ((tests_passed++))
    fi

    # Test 4: Your Protocol Endpoint (customize this)
    ((tests_total++))
    test_data='{"input_data": "test", "parameters": {"param1": "value1"}}'
    if test_endpoint "POST" "/your-endpoint" "$test_data" 200 "Protocol Endpoint"; then
        ((tests_passed++))
    fi

    # Add more protocol-specific tests here
    # Example:
    # ((tests_total++))
    # if test_endpoint "POST" "/your-other-endpoint" "$other_data" 200 "Other Endpoint"; then
    #     ((tests_passed++))
    # fi

    # Test 5: Error Handling (Invalid endpoint)
    ((tests_total++))
    if test_endpoint "GET" "/nonexistent" "" 404 "Error Handling - 404"; then
        ((tests_passed++))
    fi

    # Summary
    echo "=============================================="
    echo "📊 Test Results Summary"
    echo "=============================================="
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