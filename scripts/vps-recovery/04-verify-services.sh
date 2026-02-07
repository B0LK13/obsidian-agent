#!/bin/bash
# VPS Recovery Script - Step 4: Verify All Services
# Run after Docker services are restored

set -e
echo "=========================================="
echo "SERVICE VERIFICATION - $(hostname)"
echo "=========================================="
echo "Date: $(date)"
echo ""

TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "unknown")
echo "Tailscale IP: $TAILSCALE_IP"
echo ""

# Define services to check based on hostname
if [[ $(hostname) == *"server1"* ]] || [[ "$TAILSCALE_IP" == "100.106.57.38" ]]; then
    echo "=== VPS-1 Services ==="
    SERVICES=(
        "Teacher Agent|localhost:5005|/health"
        "n8n|localhost:5678|/"
        "Portainer|localhost:9000|/"
        "Traefik Dashboard|localhost:8080|/dashboard/"
    )
elif [[ $(hostname) == *"server2"* ]] || [[ "$TAILSCALE_IP" == "100.123.199.47" ]]; then
    echo "=== VPS-2 Services ==="
    SERVICES=(
        "Learner Agent|localhost:5006|/health"
        "Qdrant|localhost:6333|/collections"
    )
else
    echo "=== Unknown VPS - Checking common services ==="
    SERVICES=(
        "HTTP|localhost:80|/"
        "HTTPS|localhost:443|/"
    )
fi

# Check each service
echo ""
for service in "${SERVICES[@]}"; do
    IFS='|' read -r name endpoint path <<< "$service"
    echo -n "Checking $name ($endpoint$path)... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "http://$endpoint$path" 2>/dev/null || echo "000")
    
    if [[ "$response" == "200" ]] || [[ "$response" == "301" ]] || [[ "$response" == "302" ]]; then
        echo "✅ UP (HTTP $response)"
    elif [[ "$response" == "401" ]] || [[ "$response" == "403" ]]; then
        echo "✅ UP (Auth required - HTTP $response)"
    else
        echo "❌ DOWN (HTTP $response)"
    fi
done

# Check external endpoints (via Traefik/Cloudflare)
echo ""
echo "=== External Endpoints ==="
EXTERNAL_URLS=(
    "https://agent.theblackagency.cloud"
    "https://n8n.theblackagency.cloud"
    "https://dash.theblackagency.cloud"
    "https://portainer2.theblackagency.cloud"
)

for url in "${EXTERNAL_URLS[@]}"; do
    echo -n "Checking $url... "
    response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "$url" 2>/dev/null || echo "000")
    
    if [[ "$response" == "200" ]] || [[ "$response" == "301" ]] || [[ "$response" == "302" ]]; then
        echo "✅ UP (HTTP $response)"
    elif [[ "$response" == "401" ]] || [[ "$response" == "403" ]]; then
        echo "✅ UP (Auth required)"
    else
        echo "❌ DOWN (HTTP $response)"
    fi
done

# Check A2A connectivity between agents
echo ""
echo "=== A2A Agent Connectivity ==="
if [[ "$TAILSCALE_IP" == "100.106.57.38" ]]; then
    echo -n "VPS-1 → VPS-2 (Learner Agent)... "
    response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "http://100.123.199.47:5006/health" 2>/dev/null || echo "000")
    [[ "$response" == "200" ]] && echo "✅ Connected" || echo "❌ Unreachable"
elif [[ "$TAILSCALE_IP" == "100.123.199.47" ]]; then
    echo -n "VPS-2 → VPS-1 (Teacher Agent)... "
    response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "http://100.106.57.38:5005/health" 2>/dev/null || echo "000")
    [[ "$response" == "200" ]] && echo "✅ Connected" || echo "❌ Unreachable"
fi

echo ""
echo "=========================================="
echo "VERIFICATION COMPLETE"
echo "=========================================="
