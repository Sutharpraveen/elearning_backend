#!/bin/bash

# Test Cart Functionality with Curl Commands
# Update the variables below with your actual server details

SERVER_URL="http://your-server-ip:8000"
JWT_TOKEN="your-jwt-token-here"

echo "🛒 Testing Cart Functionality with Curl"
echo "======================================"

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

# Check JWT token
if [ "$JWT_TOKEN" = "your-jwt-token-here" ]; then
    echo -e "${YELLOW}🔑 Please update JWT_TOKEN with your actual JWT token${NC}"
    echo "Get token from: POST /api/users/login/"
    exit 1
fi

# Check server
echo "🏥 Testing server connectivity..."
health_response=$(curl -s "$SERVER_URL/health/")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Server is responding${NC}"
else
    echo -e "${RED}❌ Server not responding${NC}"
    exit 1
fi

# Step 1: Get cart summary (should be empty initially)
echo ""
echo "📋 Step 1: Getting cart summary..."
api_call "GET" "/api/shopping/cart/get_cart_summary/" ""

# Step 2: Add course to cart
echo "➕ Step 2: Adding course to cart..."
add_data='{"course_id": 1}'
api_call "POST" "/api/shopping/cart/add/" "$add_data"

# Step 3: Get cart summary again (should show the added course)
echo "📋 Step 3: Getting updated cart summary..."
api_call "GET" "/api/shopping/cart/get_cart_summary/" ""

# Step 4: Try to add the same course again (should fail)
echo "❌ Step 4: Trying to add same course again (should fail)..."
api_call "POST" "/api/shopping/cart/add/" "$add_data"

# Step 5: Remove course from cart
echo "➖ Step 5: Removing course from cart..."
remove_data='{"course_id": 1}'
api_call "POST" "/api/shopping/cart/remove/" "$remove_data"

# Step 6: Get final cart summary (should be empty)
echo "📋 Step 6: Getting final cart summary..."
api_call "GET" "/api/shopping/cart/get_cart_summary/" ""

echo ""
echo -e "${GREEN}🎯 Cart API test completed!${NC}"
echo "If all steps worked correctly, your cart functionality is working."
echo "If you see errors, check the responses above."
