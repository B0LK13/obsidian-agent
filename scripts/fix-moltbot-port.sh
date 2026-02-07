#!/bin/bash
docker rm -f moltbot 2>/dev/null
sed -i 's/3000:3000/3001:3000/' /opt/moltbot/docker-compose.yml
sed -i 's/server.port=3000/server.port=3001/' /opt/moltbot/docker-compose.yml
cd /opt/moltbot
docker compose up -d
sleep 3
docker ps --filter name=moltbot
curl -s http://localhost:3001/health
