#!/bin/bash
# Configure Traefik routing for Dokploy

cat > /etc/dokploy/traefik/dynamic/dokploy-route.yml << 'EOF'
http:
  routers:
    dokploy:
      rule: "Host(`dokploy.theblackagency.cloud`)"
      entryPoints:
        - websecure
      service: dokploy
      tls:
        certResolver: letsencrypt

  services:
    dokploy:
      loadBalancer:
        servers:
          - url: "http://dokploy:3000"
EOF

echo "Traefik config created. Reloading..."
docker kill -s HUP dokploy-traefik 2>/dev/null || true
sleep 2
echo "Done. Testing..."
curl -s -o /dev/null -w "%{http_code}" -H "Host: dokploy.theblackagency.cloud" http://localhost/
