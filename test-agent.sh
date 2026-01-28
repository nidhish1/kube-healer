#!/bin/bash
# Test script to generate log errors and watch the agent respond

echo "🧪 Self-Healing Agent Test Script"
echo "=================================="
echo ""

# Check if running in Docker
if [ -f "/.dockerenv" ]; then
    LOG_FILE="/tmp/test-app.log"
else
    # Running on host, need to exec into container
    echo "⚠️  This script should run inside the Docker container"
    echo "Run: docker exec -it self-healing-agent bash"
    echo "Then: ./test-agent.sh"
    exit 1
fi

# Create log file if it doesn't exist
touch $LOG_FILE

echo "📝 Log file: $LOG_FILE"
echo ""
echo "Generating test errors..."
echo ""

# Test 1: Disk Full Error
echo "Test 1: Disk Full Error"
echo "$(date) INFO: Application running normally" >> $LOG_FILE
sleep 2
echo "$(date) ERROR: No space left on device /dev/sda1" >> $LOG_FILE
echo "✅ Disk full error added"
sleep 5

# Test 2: Out of Memory
echo ""
echo "Test 2: Out of Memory Error"
echo "$(date) INFO: Processing large dataset" >> $LOG_FILE
sleep 2
echo "$(date) FATAL: OutOfMemoryError: Java heap space exhausted" >> $LOG_FILE
echo "✅ OOM error added"
sleep 5

# Test 3: Connection Refused
echo ""
echo "Test 3: Connection Error"
echo "$(date) INFO: Attempting database connection" >> $LOG_FILE
sleep 2
echo "$(date) ERROR: Connection refused to database:5432" >> $LOG_FILE
echo "✅ Connection error added"
sleep 5

# Test 4: Database Pool Exhausted
echo ""
echo "Test 4: Database Connection Pool"
echo "$(date) WARNING: Database connections: 95/100" >> $LOG_FILE
sleep 1
echo "$(date) ERROR: Too many connections to database" >> $LOG_FILE
echo "$(date) FATAL: Connection pool exhausted" >> $LOG_FILE
echo "✅ Pool exhaustion error added"
sleep 5

echo ""
echo "✅ Test complete!"
echo ""
echo "Check the agent logs to see actions taken:"
echo "  - Via Dozzle: http://localhost:9999"
echo "  - Via terminal: docker-compose logs -f agent"
echo ""
echo "Check incidents via API:"
echo "  curl http://localhost:8000/incidents"
