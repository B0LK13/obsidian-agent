#!/bin/bash
# VPS Recovery Script - Step 1: Diagnosis
# Run this via Hostinger Console (hPanel → VPS → Terminal)
# For: vps-server1.theblackagency.cloud (100.106.57.38)
#      vps-server2.theblackagency.cloud (100.123.199.47)

set -e
echo "=========================================="
echo "VPS DIAGNOSTIC SCRIPT - $(hostname)"
echo "=========================================="
echo "Date: $(date)"
echo ""

# 1. System Status
echo "=== SYSTEM STATUS ==="
uptime
free -h
df -h /
echo ""

# 2. Check SSH Service
echo "=== SSH SERVICE ==="
systemctl status sshd --no-pager || systemctl status ssh --no-pager
echo ""

# 3. Check Docker
echo "=== DOCKER STATUS ==="
systemctl status docker --no-pager
echo ""
echo "Docker containers:"
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

# 4. Check Tailscale
echo "=== TAILSCALE STATUS ==="
tailscale status || echo "Tailscale not running or not installed"
tailscale ip -4 || echo "No Tailscale IP"
echo ""

# 5. Check Firewall
echo "=== UFW FIREWALL ==="
ufw status verbose
echo ""

# 6. Check Network Interfaces
echo "=== NETWORK INTERFACES ==="
ip addr show | grep -E "inet |tailscale"
echo ""

# 7. Check Listening Ports
echo "=== LISTENING PORTS ==="
ss -tlnp | head -20
echo ""

# 8. Recent System Logs
echo "=== RECENT SYSTEM LOGS ==="
journalctl -p err --since "1 hour ago" --no-pager | tail -20
echo ""

# 9. Docker Logs (if running)
echo "=== DOCKER CONTAINER LOGS (errors) ==="
for container in $(docker ps -aq 2>/dev/null); do
    name=$(docker inspect --format '{{.Name}}' $container | sed 's/\///')
    echo "--- $name ---"
    docker logs --tail 5 $container 2>&1 | grep -i -E "error|fail|crash" || echo "No recent errors"
done
echo ""

echo "=========================================="
echo "DIAGNOSIS COMPLETE"
echo "=========================================="
