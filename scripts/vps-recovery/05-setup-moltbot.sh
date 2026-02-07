#!/bin/bash
# Moltbot Setup Script for moltbot.anoniem.cc
# Run on target VPS after base recovery is complete

set -e
echo "=========================================="
echo "MOLTBOT SETUP - moltbot.anoniem.cc"
echo "=========================================="

# Configuration
DOMAIN="moltbot.anoniem.cc"
INSTALL_DIR="/opt/moltbot"
TRAEFIK_NETWORK="traefik-public"

# 1. Create installation directory
echo "=== Creating Installation Directory ==="
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# 2. Create docker-compose.yml for Moltbot
echo "=== Creating Docker Compose Configuration ==="
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
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - BOT_PREFIX=${BOT_PREFIX:-!}
    command: ["node", "index.js"]
    networks:
      - traefik-public
      - internal
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.moltbot.rule=Host(`moltbot.anoniem.cc`)"
      - "traefik.http.routers.moltbot.entrypoints=websecure"
      - "traefik.http.routers.moltbot.tls.certresolver=letsencrypt"
      - "traefik.http.services.moltbot.loadbalancer.server.port=3000"
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  moltbot-db:
    image: postgres:16-alpine
    container_name: moltbot-db
    restart: unless-stopped
    environment:
      - POSTGRES_USER=moltbot
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=moltbot
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - internal
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U moltbot"]
      interval: 10s
      timeout: 5s
      retries: 5

  moltbot-redis:
    image: redis:7-alpine
    container_name: moltbot-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - internal
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

networks:
  traefik-public:
    external: true
  internal:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
EOF

# 3. Create .env template
echo "=== Creating Environment Template ==="
cat > .env.example << 'EOF'
# Moltbot Configuration
DISCORD_TOKEN=your_discord_bot_token
GOOGLE_API_KEY=your_google_gemini_api_key
BOT_PREFIX=!

# Database
DB_PASSWORD=secure_random_password_here

# Optional
LOG_LEVEL=info
EOF

# Copy to .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file - EDIT THIS WITH YOUR TOKENS"
fi

# 4. Create app directory structure
echo "=== Creating App Directory ==="
mkdir -p app data

# 5. Create basic health check endpoint
cat > app/health.js << 'EOF'
const http = require('http');

const server = http.createServer((req, res) => {
    if (req.url === '/health') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'healthy', service: 'moltbot' }));
    } else {
        res.writeHead(404);
        res.end();
    }
});

server.listen(3000, () => {
    console.log('Health check server running on port 3000');
});

module.exports = server;
EOF

# 6. Ensure Traefik network exists
echo "=== Ensuring Traefik Network ==="
docker network create traefik-public 2>/dev/null || echo "Network already exists"

echo ""
echo "=========================================="
echo "MOLTBOT SETUP COMPLETE"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit /opt/moltbot/.env with your tokens"
echo "2. Add your Moltbot application code to /opt/moltbot/app/"
echo "3. Run: cd /opt/moltbot && docker-compose up -d"
echo "4. Configure Cloudflare DNS for moltbot.anoniem.cc"
echo ""
