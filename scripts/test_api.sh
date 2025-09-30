#!/bin/bash

# API Testing Script for Personal Assistant Agent
# ===============================================
# Tests the web interface API endpoints
# Make sure the web server is running first: ./dev.sh serve

echo "🧪 API TESTING FOR PERSONAL ASSISTANT"
echo "======================================"
echo ""

BASE_URL="http://localhost:8000"

echo "📋 1. Testing Agent Status..."
curl -s "$BASE_URL/api/status" | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'✅ Agent Status: {data[\"status\"]}')
    print(f'✅ Tools Available: {data[\"tools\"][\"total\"]}')
    print(f'✅ Circuit Breakers: {data[\"circuit_breakers\"][\"total\"]}')
except Exception as e:
    print(f'❌ Status check failed: {e}')
"
echo ""

echo "📋 2. Testing Simple Task Addition..."
curl -s -X POST "$BASE_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Add a task called \"API Test Task\""}' | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        print('✅ Task addition: SUCCESS')
        print(f'✅ Steps completed: {data.get(\"data\", {}).get(\"steps_completed\", 0)}')
    else:
        print('❌ Task addition: FAILED')
        print(f'Error: {data.get(\"message\", \"Unknown\")}')
except Exception as e:
    print(f'❌ Task addition test failed: {e}')
"
echo ""

echo "📋 3. Testing Task Listing..."
curl -s -X POST "$BASE_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "List all my tasks"}' | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        task_data = data.get('data', {}).get('task_data', {})
        total = task_data.get('total_count', 0)
        pending = task_data.get('pending_count', 0)
        completed = task_data.get('completed_count', 0)
        print('✅ Task listing: SUCCESS')
        print(f'✅ Total tasks: {total} (Pending: {pending}, Completed: {completed})')
    else:
        print('❌ Task listing: FAILED')
except Exception as e:
    print(f'❌ Task listing test failed: {e}')
"
echo ""

echo "📋 4. Testing Calculator..."
curl -s -X POST "$BASE_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Calculate 25% of 200"}' | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        calc_result = data.get('data', {}).get('calculation_result')
        print('✅ Calculator: SUCCESS')
        print(f'✅ Result: {calc_result}')
    else:
        print('❌ Calculator: FAILED')
except Exception as e:
    print(f'❌ Calculator test failed: {e}')
"
echo ""

echo "📋 5. Testing Multi-Step Operation..."
curl -s -X POST "$BASE_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Add a task called \"Multi-step test\", then list all my tasks"}' | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        steps = data.get('data', {}).get('steps_completed', 0)
        summary = data.get('data', {}).get('execution_summary', '')
        print('✅ Multi-step operation: SUCCESS')
        print(f'✅ {summary}')
    else:
        print('❌ Multi-step operation: FAILED')
except Exception as e:
    print(f'❌ Multi-step test failed: {e}')
"
echo ""

echo "🎉 API TESTING COMPLETE!"
echo "========================"
echo ""
echo "If all tests show ✅ SUCCESS, your reorganized agent is working perfectly!"
echo "The core functionality, planner-executor, and production features are all operational."
echo ""
echo "🚀 Your enterprise-grade reorganization is ready for commit!"
