#!/bin/bash
# Complete VPS Setup Script
# Run in Hostinger Console: hPanel -> VPS -> Terminal
# Works for both VPS-1 (168.231.86.24) and vps-server1-1

set -e

echo "=========================================="
echo "VPS Complete Setup - The Black Agency"
echo "=========================================="

# 1. Fix UFW to allow SSH
echo "[1/6] Configuring UFW Firewall..."
ufw disable 2>/dev/null || true
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 41641/udp
ufw --force enable
echo "UFW configured."

# 2. Restart SSH
echo "[2/6] Restarting SSH..."
systemctl restart ssh || systemctl restart sshd
echo "SSH restarted."

# 3. Install Tailscale if not present
echo "[3/6] Installing Tailscale..."
if ! command -v tailscale &> /dev/null; then
    curl -fsSL https://tailscale.com/install.sh | sh
fi
echo "Tailscale installed."

# 4. Enable Tailscale with SSH
echo "[4/6] Enabling Tailscale SSH..."
tailscale up --ssh --accept-routes
echo "Tailscale SSH enabled."

# 5. Configure UFW for Tailscale interface
echo "[5/6] Configuring UFW for Tailscale..."
if ip link show tailscale0 &>/dev/null; then
    ufw allow in on tailscale0
    ufw allow out on tailscale0
    ufw reload
fi
echo "Tailscale UFW rules added."

# 6. Show status
echo "[6/6] Final Status..."
echo ""
echo "=== Tailscale Status ==="
tailscale status
echo ""
echo "=== UFW Status ==="
ufw status verbose
echo ""
echo "=== Docker Containers ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Docker not running"
echo ""
echo "=== SSH Status ==="
systemctl status ssh --no-pager 2>/dev/null || systemctl status sshd --no-pager
echo ""
echo "=========================================="
echo "SETUP COMPLETE!"
echo "Tailscale IP: $(tailscale ip -4)"
echo "=========================================="
