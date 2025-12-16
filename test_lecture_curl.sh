#!/bin/bash

# Test Lecture Creation with Curl Commands
# Update the variables below with your actual server details

SERVER_URL="http://your-server-ip:8000"
JWT_TOKEN="your-jwt-token-here"

echo "🎬 Testing Lecture Creation with Curl"
echo "====================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to make API calls
api_call() {
    local method=$1
    local url=$2
    local data=$3

    echo -e "${YELLOW}$method $url${NC}"

    if [ "$method" = "GET" ]; then
        response=$(curl -s -X GET "$SERVER_URL$url" \
            -H "Authorization: Bearer $JWT_TOKEN" \
            -H "Content-Type: application/json")
    else
        response=$(curl -s -X $method "$SERVER_URL$url" \
            -H "Authorization: Bearer $JWT_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi

    # Check if response is valid JSON
    if echo "$response" | jq . >/dev/null 2>&1; then
        echo "$response" | jq .
    else
        echo "$response"
    fi
    echo ""
}

# Step 1: Test server health
echo "🏥 Testing server health..."
health_response=$(curl -s "$SERVER_URL/health/")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Server is responding${NC}"
else
    echo -e "${RED}❌ Server not responding${NC}"
    exit 1
fi

# Step 2: Get authentication token (if not provided)
if [ "$JWT_TOKEN" = "your-jwt-token-here" ]; then
    echo ""
    echo -e "${YELLOW}🔑 Getting JWT Token...${NC}"
    echo "Update JWT_TOKEN in this script with your actual token"
    echo "To get token: POST /api/users/login/ with your credentials"
    exit 1
fi

# Step 3: Get courses
echo ""
echo "📚 Getting available courses..."
api_call "GET" "/api/courses/courses/" ""

# Step 4: Get sections for first course
echo "📖 Getting sections for course ID 1..."
api_call "GET" "/api/courses/1/sections/" ""

# Step 5: Create a lecture
echo "📝 Creating a new lecture..."
lecture_data='{
  "title": "Test Lecture from Curl",
  "description": "This lecture was created using curl command for testing",
  "order": 1,
  "is_preview": false
}'

api_call "POST" "/api/courses/1/sections/1/lectures/" "$lecture_data"

# Step 6: Get lectures to verify creation
echo "📋 Verifying lecture creation..."
api_call "GET" "/api/courses/1/sections/1/lectures/" ""

echo ""
echo -e "${GREEN}🎯 Test completed!${NC}"
echo "If you see lecture data above, creation is working."
echo "If you see errors, check the troubleshooting guide."
