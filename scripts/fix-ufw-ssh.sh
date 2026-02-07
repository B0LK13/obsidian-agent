#!/bin/bash
# Fix UFW SSH Access
# Run this in Hostinger Console (hPanel -> VPS -> Terminal)

echo "=== Fixing UFW SSH Access ==="

# Disable UFW temporarily
ufw disable

# Reset UFW rules
ufw --force reset

# Set default policies
ufw default deny incoming
ufw default allow outgoing

# Allow SSH from anywhere (required for initial access)
ufw allow 22/tcp

# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow Tailscale
ufw allow 41641/udp

# Allow Tailscale interface if exists
if ip link show tailscale0 &>/dev/null; then
    ufw allow in on tailscale0
    ufw allow out on tailscale0
fi

# Enable UFW
ufw --force enable

# Show status
echo ""
echo "=== UFW Status ==="
ufw status verbose

# Restart SSH
systemctl restart ssh

echo ""
echo "=== SSH Status ==="
systemctl status ssh --no-pager

echo ""
echo "=== Done! SSH should now be accessible ==="
