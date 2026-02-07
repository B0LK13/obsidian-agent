#!/bin/bash
# VPS Recovery Script - Step 2: Fix SSH & Firewall
# Run this via Hostinger Console (hPanel → VPS → Terminal)

set -e
echo "=========================================="
echo "FIXING SSH & FIREWALL - $(hostname)"
echo "=========================================="

# 1. Ensure SSH is running
echo "=== Starting SSH Service ==="
systemctl enable ssh sshd 2>/dev/null || true
systemctl start ssh sshd 2>/dev/null || true
systemctl status sshd --no-pager || systemctl status ssh --no-pager

# 2. Fix UFW Rules for Tailscale
echo ""
echo "=== Configuring UFW for Tailscale ==="

# Reset to safe defaults if needed (uncomment if firewall is broken)
# ufw --force reset
# ufw default deny incoming
# ufw default allow outgoing

# Allow all traffic on Tailscale interface
ufw allow in on tailscale0
ufw allow out on tailscale0

# Allow SSH on Tailscale interface only (more secure)
ufw allow in on tailscale0 to any port 22 proto tcp

# Allow HTTP/HTTPS for Traefik
ufw allow 80/tcp
ufw allow 443/tcp

# Allow Tailscale UDP (for direct connections)
ufw allow 41641/udp

# Enable UFW if not already
ufw --force enable

echo ""
echo "=== Current UFW Rules ==="
ufw status numbered

# 3. Restart Tailscale with SSH enabled
echo ""
echo "=== Restarting Tailscale ==="
systemctl restart tailscaled
sleep 3

# Re-authenticate and enable SSH
tailscale up --ssh --accept-routes --accept-dns=false

echo ""
echo "=== Tailscale Status ==="
tailscale status

# 4. Test SSH locally
echo ""
echo "=== Testing SSH Locally ==="
nc -zv 127.0.0.1 22 && echo "SSH port 22 is open locally" || echo "SSH port 22 NOT open"

TAILSCALE_IP=$(tailscale ip -4)
nc -zv $TAILSCALE_IP 22 && echo "SSH on Tailscale IP ($TAILSCALE_IP) is open" || echo "SSH on Tailscale IP NOT open"

echo ""
echo "=========================================="
echo "SSH & FIREWALL FIX COMPLETE"
echo "=========================================="
echo ""
echo "You should now be able to SSH via:"
echo "  ssh root@$TAILSCALE_IP"
echo ""
