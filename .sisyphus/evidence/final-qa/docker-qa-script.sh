#!/bin/bash
# F3: Real Manual QA Script (For Docker-Enabled Environments)
# This script automates the full QA suite when Docker is available

set -e

echo "=========================================="
echo "F3: Multi-Agent RAG System - Full QA Suite"
echo "=========================================="
echo ""

# Phase 1: Service Startup
echo "Phase 1: Starting Services..."
docker compose down -v
docker compose up -d --build

echo "Waiting for services to become healthy (max 120s)..."
for i in {1..24}; do
  sleep 5
  healthy=$(docker compose ps --format json | python3 -c "import sys,json; services = [json.loads(l) for l in sys.stdin]; healthy = [s for s in services if 'healthy' in s.get('Health','') or s.get('State','')=='running']; print(len(healthy))" 2>/dev/null || echo "0")
  echo "Attempt $i: $healthy/8 services healthy"
  if [ "$healthy" -eq 8 ]; then
    echo "✅ All services ready!"
    break
  fi
done

echo ""
echo "Phase 2: Critical QA Scenarios"
echo "=========================================="

# Scenario 1: Health Check
echo ""
echo "[1/8] Testing Health Check..."
response=$(curl -sf http://localhost/api/v1/health)
if echo "$response" | grep -q '"status":"ok"'; then
  echo "✅ PASS: Health check returned ok status"
else
  echo "❌ FAIL: Health check failed"
fi

# Scenario 2: Single Department Query
echo ""
echo "[2/8] Testing Single Department Query (IT Support)..."
response=$(curl -s -X POST http://localhost/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key" \
  -d '{"message": "How do I reset my VPN password?", "session_id": "qa-1", "department": "it_support"}')
sources=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('sources',[])))" 2>/dev/null || echo "0")
if [ "$sources" -gt 0 ]; then
  echo "✅ PASS: Got $sources sources from IT Support"
else
  echo "❌ FAIL: No sources returned"
fi

# Scenario 3: SSE Streaming
echo ""
echo "[3/8] Testing SSE Streaming..."
stream_output=$(curl -sN -X POST http://localhost/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key" \
  -d '{"message": "What is the baggage weight limit?", "session_id": "qa-2"}' \
  --max-time 10 | head -n 5)
event_count=$(echo "$stream_output" | grep -c "^data:" || true)
if [ "$event_count" -gt 1 ]; then
  echo "✅ PASS: Received $event_count SSE events (streaming works)"
else
  echo "❌ FAIL: No streaming events detected"
fi

# Scenario 4: Cross-Department Query
echo ""
echo "[4/8] Testing Cross-Department Query..."
response=$(curl -s -X POST http://localhost/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key" \
  -d '{"message": "My flight was delayed and I need a refund on my credit card", "session_id": "qa-3"}')
dept_count=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); sources = d.get('sources',[]); depts = set(s.get('department','') for s in sources); print(len(depts))" 2>/dev/null || echo "0")
if [ "$dept_count" -ge 2 ]; then
  echo "✅ PASS: Multiple departments detected ($dept_count)"
else
  echo "⚠️  WARNING: Only $dept_count department(s) detected"
fi

# Scenario 5: Frontend Check (without Playwright)
echo ""
echo "[5/8] Testing Frontend Availability..."
frontend_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/)
if [ "$frontend_status" -eq 200 ]; then
  echo "✅ PASS: Frontend accessible at http://localhost/"
else
  echo "❌ FAIL: Frontend returned $frontend_status"
fi

# Scenario 6: RAGAS Evaluation Trigger
echo ""
echo "[6/8] Testing RAGAS Evaluation Trigger..."
response=$(curl -s -X POST http://localhost/api/v1/evaluation/trigger \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key" \
  -d '{"session_id": "qa-1"}')
job_id=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('job_id',''))" 2>/dev/null || echo "")
if [ -n "$job_id" ]; then
  echo "✅ PASS: Evaluation job triggered (job_id: $job_id)"
else
  echo "❌ FAIL: No job_id returned"
fi

# Scenario 7: Embedding Mode Check
echo ""
echo "[7/8] Testing Embedding Mode..."
embedding_model=$(docker compose exec -T api python -c "from app.core.embeddings import get_embedding_model; m = get_embedding_model(); print(type(m).__name__)" 2>/dev/null || echo "unknown")
if echo "$embedding_model" | grep -q "HuggingFace"; then
  echo "✅ PASS: Using HuggingFace embeddings (local mode)"
else
  echo "⚠️  INFO: Embedding model: $embedding_model"
fi

# Scenario 8: Persistence Test
echo ""
echo "[8/8] Testing Data Persistence..."
# First query
sources_before=$(curl -s -X POST http://localhost/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key" \
  -d '{"message": "VPN setup", "session_id": "persist-test", "department": "it_support"}' | \
  python3 -c "import sys,json; print(len(json.load(sys.stdin).get('sources',[])))" 2>/dev/null || echo "0")

# Restart API
docker compose restart api
sleep 15

# Second query
sources_after=$(curl -s -X POST http://localhost/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key" \
  -d '{"message": "VPN troubleshooting", "session_id": "persist-test", "department": "it_support"}' | \
  python3 -c "import sys,json; print(len(json.load(sys.stdin).get('sources',[])))" 2>/dev/null || echo "0")

if [ "$sources_before" -gt 0 ] && [ "$sources_after" -gt 0 ]; then
  echo "✅ PASS: Data persisted after restart"
else
  echo "❌ FAIL: Data persistence issue (before: $sources_before, after: $sources_after)"
fi

echo ""
echo "Phase 3: Edge Case Testing"
echo "=========================================="

# Edge Case 1: Empty Message
echo ""
echo "[1/3] Testing Empty Message..."
response=$(curl -s -X POST http://localhost/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key" \
  -d '{"message": "", "session_id": "edge-1"}')
if echo "$response" | grep -q "detail"; then
  echo "✅ PASS: Validation error returned for empty message"
else
  echo "❌ FAIL: Empty message not handled"
fi

# Edge Case 2: Invalid API Key
echo ""
echo "[2/3] Testing Invalid API Key..."
http_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: wrong-key" \
  -d '{"message": "test", "session_id": "edge-2"}')
if [ "$http_code" -eq 403 ] || [ "$http_code" -eq 401 ]; then
  echo "✅ PASS: Invalid API key rejected ($http_code)"
else
  echo "❌ FAIL: Invalid API key returned $http_code"
fi

# Edge Case 3: Malformed JSON
echo ""
echo "[3/3] Testing Malformed JSON..."
http_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key" \
  -d 'invalid json')
if [ "$http_code" -eq 422 ] || [ "$http_code" -eq 400 ]; then
  echo "✅ PASS: Malformed JSON rejected ($http_code)"
else
  echo "❌ FAIL: Malformed JSON returned $http_code"
fi

echo ""
echo "=========================================="
echo "QA Suite Complete!"
echo "=========================================="
echo ""
echo "Review logs and verify all tests passed."
echo "Frontend available at: http://localhost"
echo "API documentation at: http://localhost/api/docs"
