#!/bin/bash
cd /opt/moltbot

# Update docker-compose with correct Traefik config
cat > docker-compose.yml << 'EOF'
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
    expose:
      - "3000"
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
EOF

docker compose down
docker compose up -d
sleep 3
docker ps --filter name=moltbot
curl -s http://localhost:3000/health || echo "Internal check"
curl -s -H "Host: moltbot.theblackagency.cloud" http://localhost/health || echo "Traefik not routing yet"
