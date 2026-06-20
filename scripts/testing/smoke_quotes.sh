#!/usr/bin/env bash
set -e

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

echo "Login as demo..."
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123"}' \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "Failed to login as demo"
  exit 1
fi

echo "List operations..."
OP_ID=$(curl -s "$BASE_URL/api/operations" -H "Authorization: Bearer $TOKEN" | grep -o '"id":"[^"]*' | head -n 1 | cut -d'"' -f4)

if [ -z "$OP_ID" ]; then
  echo "No operation found, testing with fallback test-op-1..."
  OP_ID="test-op-1"
fi

echo "Creating quote share link for $OP_ID..."
SHARE_RES=$(curl -s -X POST "$BASE_URL/api/quotes/share" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"operation_id\":\"$OP_ID\"}")

QUOTE_TOKEN=$(echo $SHARE_RES | grep -o '"token":"[^"]*' | cut -d'"' -f4)

if [ -z "$QUOTE_TOKEN" ]; then
  echo "Failed to create quote. Response: $SHARE_RES"
  exit 1
fi

echo "Fetching public quote..."
PUBLIC_RES=$(curl -s "$BASE_URL/api/quotes/public/$QUOTE_TOKEN")

if ! echo $PUBLIC_RES | grep -q "costo_total"; then
  echo "Quote missing costo_total! Response: $PUBLIC_RES"
  exit 1
fi
echo "Public quote valid."

echo "Rate limit test (11 requests)..."
for i in {1..11}; do
  RES=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/quotes/public/$QUOTE_TOKEN")
  echo "Req $i: $RES"
  if [ "$i" -eq 11 ]; then
    if [ "$RES" != "429" ]; then
      echo "Rate limit failed! Expected 429, got $RES"
      exit 1
    fi
  fi
done

echo "Smoke test passed successfully!"
