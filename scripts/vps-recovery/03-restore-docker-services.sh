#!/bin/bash
# VPS Recovery Script - Step 3: Restore Docker Services
# Run this via Hostinger Console or SSH after firewall is fixed

set -e
echo "=========================================="
echo "RESTORING DOCKER SERVICES - $(hostname)"
echo "=========================================="

# 1. Check Docker daemon
echo "=== Checking Docker Daemon ==="
systemctl status docker --no-pager || {
    echo "Docker not running, starting..."
    systemctl start docker
    sleep 5
}

# 2. Check current container status
echo ""
echo "=== Current Container Status ==="
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"

# 3. Identify and restart stopped containers
echo ""
echo "=== Restarting Stopped Containers ==="
STOPPED=$(docker ps -a --filter "status=exited" --filter "status=dead" -q)
if [ -n "$STOPPED" ]; then
    echo "Found stopped containers, restarting..."
    docker start $STOPPED
else
    echo "No stopped containers found"
fi

# 4. Restart Docker Compose stacks
echo ""
echo "=== Restarting Docker Compose Stacks ==="

# Agent Zero stack (VPS-1)
if [ -d "/opt/agent-zero" ]; then
    echo "Restarting Agent Zero stack..."
    cd /opt/agent-zero
    docker-compose down 2>/dev/null || docker compose down 2>/dev/null || true
    docker-compose up -d 2>/dev/null || docker compose up -d 2>/dev/null
fi

# Learner Agent stack (VPS-2)
if [ -d "/opt/learner-agent" ]; then
    echo "Restarting Learner Agent stack..."
    cd /opt/learner-agent
    docker-compose down 2>/dev/null || docker compose down 2>/dev/null || true
    docker-compose up -d 2>/dev/null || docker compose up -d 2>/dev/null
fi

# Traefik (if separate)
if [ -d "/opt/traefik" ]; then
    echo "Restarting Traefik..."
    cd /opt/traefik
    docker-compose down 2>/dev/null || docker compose down 2>/dev/null || true
    docker-compose up -d 2>/dev/null || docker compose up -d 2>/dev/null
fi

# n8n stack
if [ -d "/opt/n8n" ]; then
    echo "Restarting n8n..."
    cd /opt/n8n
    docker-compose down 2>/dev/null || docker compose down 2>/dev/null || true
    docker-compose up -d 2>/dev/null || docker compose up -d 2>/dev/null
fi

# Qdrant (VPS-2)
if [ -d "/opt/qdrant" ]; then
    echo "Restarting Qdrant..."
    cd /opt/qdrant
    docker-compose down 2>/dev/null || docker compose down 2>/dev/null || true
    docker-compose up -d 2>/dev/null || docker compose up -d 2>/dev/null
fi

# 5. Wait for containers to start
echo ""
echo "Waiting 15 seconds for containers to initialize..."
sleep 15

# 6. Verify container status
echo ""
echo "=== Final Container Status ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 7. Check container health
echo ""
echo "=== Container Health ==="
docker ps --filter "health=unhealthy" --format "{{.Names}}: UNHEALTHY" || echo "All containers healthy"

# 8. Test service endpoints
echo ""
echo "=== Testing Local Endpoints ==="

# Test common ports
for port in 80 443 5005 5006 5678 6333 9000; do
    nc -zv 127.0.0.1 $port 2>&1 | grep -q "succeeded" && echo "Port $port: OPEN" || echo "Port $port: CLOSED"
done

echo ""
echo "=========================================="
echo "DOCKER SERVICES RESTORATION COMPLETE"
echo "=========================================="
