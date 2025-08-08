#!/bin/bash
# Test commands for ACP agents
# Run these commands to test any ACP-compliant agent

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default agent URL
AGENT_URL=${AGENT_URL:-"http://localhost:8000"}

echo -e "${BLUE}🧪 Testing ACP Agent at: $AGENT_URL${NC}"
echo "=============================================="

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo -e "\n${YELLOW}Testing $description${NC}"
    echo "Endpoint: $method $endpoint"
    
    if [ -n "$data" ]; then
        echo "Data: $data"
        response=$(curl -s -X $method "$AGENT_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" \
            -w "HTTPSTATUS:%{http_code}")
    else
        response=$(curl -s -X $method "$AGENT_URL$endpoint" \
            -w "HTTPSTATUS:%{http_code}")
    fi
    
    # Extract HTTP status and body
    http_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS:.*//g')
    
    # Check status
    if [ $http_code -eq 200 ]; then
        echo -e "${GREEN}✓ Status: $http_code${NC}"
        echo "Response: $body" | jq . 2>/dev/null || echo "Response: $body"
    else
        echo -e "${RED}✗ Status: $http_code${NC}"
        echo "Response: $body"
    fi
}

# Test 1: Health check (optional but recommended)
echo -e "\n${BLUE}1. Health Check (Optional)${NC}"
test_endpoint "GET" "/health" "" "Health Check"

# Test 2: Authentication endpoint
echo -e "\n${BLUE}2. Authentication Endpoint (Required)${NC}"
test_endpoint "GET" "/auth" "" "Authentication Info"

# Test 3: Schema endpoint  
echo -e "\n${BLUE}3. Schema Endpoint (Required)${NC}"
test_endpoint "GET" "/schema" "" "Input/Output Schemas"

# Test 4: Capabilities endpoint
echo -e "\n${BLUE}4. Capabilities Endpoint (Required)${NC}"
test_endpoint "GET" "/capabilities" "" "Agent Capabilities"

# Test 5: Configuration creation
echo -e "\n${BLUE}5. Configuration Endpoint (Required)${NC}"
config_response=$(curl -s -X POST "$AGENT_URL/config" \
    -H "Content-Type: application/json" \
    -d '{"config": {"prefix": "Test: ", "language": "en"}}')

# Extract config_id for later use
config_id=$(echo "$config_response" | jq -r '.config_id // "unknown"')
echo "Config ID: $config_id"

test_endpoint "POST" "/config" '{"config": {"prefix": "Test: ", "language": "en"}}' "Create Configuration"

# Test 6: Basic invocation
echo -e "\n${BLUE}6. Invocation Endpoint (Required)${NC}"
test_endpoint "POST" "/invoke" '{"input": {"message": "Hello from test!"}}' "Basic Invocation"

# Test 7: Invocation with config (if we got a config_id)
if [ "$config_id" != "unknown" ] && [ "$config_id" != "null" ]; then
    echo -e "\n${BLUE}7. Invocation with Configuration${NC}"
    test_endpoint "POST" "/invoke" "{\"input\": {\"message\": \"Configured test!\"}, \"config_id\": \"$config_id\"}" "Invocation with Config"
fi

# Test 8: Streaming endpoint (optional)
echo -e "\n${BLUE}8. Streaming Endpoint (Optional)${NC}"
echo "Testing streaming endpoint (if available)..."
streaming_response=$(curl -s -X POST "$AGENT_URL/invoke/stream" \
    -H "Content-Type: application/json" \
    -d '{"input": {"message": "Stream test"}}' \
    -w "HTTPSTATUS:%{http_code}" \
    --max-time 10)

stream_status=$(echo $streaming_response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
if [ $stream_status -eq 200 ]; then
    echo -e "${GREEN}✓ Streaming supported${NC}"
else
    echo -e "${YELLOW}⚠ Streaming not available (optional feature)${NC}"
fi

# Test 9: Error handling
echo -e "\n${BLUE}9. Error Handling Test${NC}"
test_endpoint "POST" "/invoke" '{"invalid": "data"}' "Invalid Input (should return 400)"

# Test 10: Non-existent endpoint
echo -e "\n${BLUE}10. Non-existent Endpoint Test${NC}"
test_endpoint "GET" "/nonexistent" "" "Non-existent Endpoint (should return 404)"

# Summary
echo -e "\n${BLUE}=============================================="
echo -e "🎯 ACP Compliance Test Summary${NC}"
echo "=============================================="

echo -e "${GREEN}Required Endpoints:${NC}"
echo "✓ GET  /auth         - Authentication info"
echo "✓ GET  /schema       - Data schemas" 
echo "✓ POST /config       - Configuration management"
echo "✓ POST /invoke       - Agent execution"
echo "✓ GET  /capabilities - Agent capabilities"

echo -e "\n${YELLOW}Optional Endpoints:${NC}"
echo "⚠ GET  /health       - Health check"
echo "⚠ POST /invoke/stream - Streaming responses"

echo -e "\n${BLUE}Manual Test Commands:${NC}"
echo "# Basic invocation"
echo "curl -X POST \"$AGENT_URL/invoke\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"input\": {\"message\": \"Hello!\"}}'"

echo -e "\n# Create configuration"
echo "curl -X POST \"$AGENT_URL/config\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"config\": {\"prefix\": \"Custom: \"}}'"

echo -e "\n# Get capabilities"
echo "curl \"$AGENT_URL/capabilities\" | jq"

echo -e "\n${GREEN}✅ ACP compliance test completed!${NC}"
echo "Agent URL: $AGENT_URL"
echo "OpenAPI docs: $AGENT_URL/docs"