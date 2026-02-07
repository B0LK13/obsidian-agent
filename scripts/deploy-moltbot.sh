#!/bin/bash
# Deploy Moltbot to VPS-1 (168.231.86.24)
# Run via SSH: ssh root@168.231.86.24 'bash -s' < deploy-moltbot.sh

set -e

echo "=========================================="
echo "Deploying Moltbot to theblackagency.cloud"
echo "=========================================="

# Create directory
mkdir -p /opt/moltbot/app /opt/moltbot/data
cd /opt/moltbot

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: "3.8"

services:
  moltbot:
    image: node:20-alpine
    container_name: moltbot
    restart: unless-stopped
    working_dir: /app
    volumes:
      - ./app:/app
      - ./data:/app/data
    environment:
      - NODE_ENV=production
    command: ["node", "index.js"]
    ports:
      - "3000:3000"
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.moltbot.rule=Host(\`moltbot.theblackagency.cloud\`)"
      - "traefik.http.routers.moltbot.entrypoints=websecure"
      - "traefik.http.routers.moltbot.tls.certresolver=letsencrypt"
      - "traefik.http.services.moltbot.loadbalancer.server.port=3000"
    networks:
      - dokploy-network
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  dokploy-network:
    external: true
EOF

# Create basic app with health endpoint
cat > app/index.js << 'EOF'
const http = require('http');

const PORT = process.env.PORT || 3000;

const server = http.createServer((req, res) => {
    if (req.url === '/health') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ 
            status: 'healthy', 
            service: 'moltbot',
            timestamp: new Date().toISOString()
        }));
    } else if (req.url === '/') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ 
            name: 'Moltbot',
            version: '1.0.0',
            status: 'running'
        }));
    } else {
        res.writeHead(404);
        res.end('Not Found');
    }
});

server.listen(PORT, () => {
    console.log(`Moltbot running on port ${PORT}`);
});
EOF

# Create package.json
cat > app/package.json << 'EOF'
{
  "name": "moltbot",
  "version": "1.0.0",
  "main": "index.js",
  "scripts": {
    "start": "node index.js"
  }
}
EOF

# Check if dokploy-network exists
docker network inspect dokploy-network >/dev/null 2>&1 || docker network create dokploy-network

# Deploy
echo "Starting moltbot..."
docker-compose down 2>/dev/null || true
docker-compose up -d

# Wait for container
sleep 5

# Verify
echo ""
echo "Container status:"
docker ps --filter "name=moltbot" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "Testing health endpoint..."
curl -s http://localhost:3000/health | jq . 2>/dev/null || curl -s http://localhost:3000/health

echo ""
echo "=========================================="
echo "Moltbot deployed successfully!"
echo "URL: https://moltbot.theblackagency.cloud"
echo "=========================================="
