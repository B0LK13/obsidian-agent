#!/bin/bash
# Deploy Moltbot to VPS

mkdir -p /opt/moltbot/app /opt/moltbot/data
cd /opt/moltbot

# Create docker-compose.yml
cat > docker-compose.yml << 'COMPOSEEOF'
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
      - "traefik.http.routers.moltbot.rule=Host(`moltbot.theblackagency.cloud`)"
      - "traefik.http.routers.moltbot.entrypoints=websecure"
      - "traefik.http.routers.moltbot.tls.certresolver=letsencrypt"
      - "traefik.http.services.moltbot.loadbalancer.server.port=3000"
    networks:
      - dokploy-network
networks:
  dokploy-network:
    external: true
COMPOSEEOF

# Create basic app
cat > app/index.js << 'APPEOF'
const http = require('http');
const PORT = process.env.PORT || 3000;

const server = http.createServer((req, res) => {
    if (req.url === '/health') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'healthy', service: 'moltbot', timestamp: new Date().toISOString() }));
    } else if (req.url === '/') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ name: 'Moltbot', version: '1.0.0', status: 'running' }));
    } else {
        res.writeHead(404);
        res.end('Not Found');
    }
});

server.listen(PORT, () => console.log('Moltbot running on port ' + PORT));
APPEOF

# Create package.json
cat > app/package.json << 'PKGEOF'
{"name":"moltbot","version":"1.0.0","main":"index.js"}
PKGEOF

# Deploy
docker compose down 2>/dev/null || true
docker compose up -d

echo "Moltbot deployed!"
docker ps --filter "name=moltbot"
