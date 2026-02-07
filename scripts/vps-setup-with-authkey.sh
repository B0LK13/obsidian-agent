#!/bin/bash
# VPS Setup with Tailscale Auth Key
# Run in Hostinger Console: hPanel -> VPS -> Terminal

set -e

TS_AUTHKEY="tskey-auth-kQetsV5kDV11CNTRL-2dAYfLSSMk2TweC2EFomj2seFnATR8orT"

echo "=========================================="
echo "VPS Setup - The Black Agency"
echo "=========================================="

# 1. Fix UFW
echo "[1/5] Configuring UFW..."
ufw disable 2>/dev/null || true
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 41641/udp
ufw --force enable

# 2. Restart SSH
echo "[2/5] Restarting SSH..."
systemctl restart ssh 2>/dev/null || systemctl restart sshd 2>/dev/null || true

# 3. Install Tailscale
echo "[3/5] Installing Tailscale..."
if ! command -v tailscale &> /dev/null; then
    curl -fsSL https://tailscale.com/install.sh | sh
fi

# 4. Connect with auth key and enable SSH
echo "[4/5] Connecting Tailscale with SSH..."
tailscale up --authkey="$TS_AUTHKEY" --ssh --accept-routes

# 5. UFW for Tailscale
echo "[5/5] Configuring UFW for Tailscale..."
sleep 2
if ip link show tailscale0 &>/dev/null; then
    ufw allow in on tailscale0
    ufw reload
fi

echo ""
echo "=========================================="
echo "SETUP COMPLETE!"
echo "Tailscale IP: $(tailscale ip -4)"
echo "Hostname: $(hostname)"
echo "=========================================="
tailscale status
