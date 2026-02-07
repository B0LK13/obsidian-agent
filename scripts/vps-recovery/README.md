# VPS Recovery Scripts

Recovery scripts for theblackagency.cloud VPS infrastructure.

## VPS Fleet Status

| VPS | Tailscale IP | Public Domain | Status |
|-----|--------------|---------------|--------|
| VPS-1 | 100.106.57.38 | vps-server1.theblackagency.cloud | ⚠️ Recovery needed |
| VPS-2 | 100.123.199.47 | vps-server2.theblackagency.cloud | ⚠️ Recovery needed |

## Recovery Procedure

### Step 1: Access VPS via Hostinger Console

1. Log in to [Hostinger hPanel](https://hpanel.hostinger.com)
2. Navigate to VPS → Select your VPS
3. Click **Terminal** or **VNC** for console access

### Step 2: Run Recovery Scripts

Execute scripts in order:

```bash
# 1. Diagnose the issue
curl -sL https://raw.githubusercontent.com/YOUR_REPO/scripts/vps-recovery/01-diagnose.sh | bash

# Or copy/paste the script content directly into the console
```

**Script Order:**
1. `01-diagnose.sh` - Identify what's broken
2. `02-fix-ssh-firewall.sh` - Restore SSH access via Tailscale
3. `03-restore-docker-services.sh` - Restart Docker containers
4. `04-verify-services.sh` - Confirm everything is working
5. `05-setup-moltbot.sh` - (Optional) Set up moltbot.anoniem.cc
6. `06-cloudflare-dns-setup.sh` - Configure Cloudflare DNS

### Step 3: Verify Recovery

After running scripts, test from your local machine:

```bash
# Test SSH via Tailscale
ssh root@100.106.57.38  # VPS-1
ssh root@100.123.199.47  # VPS-2

# Test services
curl -I https://agent.theblackagency.cloud
curl -I https://n8n.theblackagency.cloud
```

## Service Architecture

### VPS-1 (100.106.57.38)
- **Teacher Agent** - Port 5005 - https://agent.theblackagency.cloud
- **n8n** - Port 5678 - https://n8n.theblackagency.cloud
- **Portainer** - Port 9000 - https://portainer2.theblackagency.cloud
- **Dashboard** - Port 80/443 - https://dash.theblackagency.cloud
- **Traefik** - Reverse proxy

### VPS-2 (100.123.199.47)
- **Learner Agent** - Port 5006
- **Qdrant** - Port 6333

### Moltbot (New)
- **Domain**: moltbot.anoniem.cc
- **Stack**: Node.js + PostgreSQL + Redis
- **Proxy**: Via Traefik with Let's Encrypt SSL

## Firewall Rules (UFW)

Required rules for proper operation:

```bash
# Allow Tailscale interface (all traffic)
ufw allow in on tailscale0
ufw allow out on tailscale0

# Allow HTTP/HTTPS for Traefik
ufw allow 80/tcp
ufw allow 443/tcp

# Allow Tailscale UDP for direct connections
ufw allow 41641/udp
```

## Troubleshooting

### SSH Connection Timeout
- Use Hostinger Console to access VPS
- Check `systemctl status sshd`
- Verify UFW allows SSH on tailscale0

### Docker Containers Not Starting
- Check `docker logs <container_name>`
- Verify disk space: `df -h`
- Check Docker daemon: `systemctl status docker`

### Tailscale in Relay Mode
- Ensure UDP 41641 is allowed
- Try `tailscale up --force-reauth`
- Check NAT/firewall on network level

### Services Unreachable via Domain
- Verify Traefik is running: `docker logs traefik`
- Check Cloudflare DNS propagation
- Verify SSL certificates: `docker exec traefik cat /letsencrypt/acme.json`

## Quick Commands

```bash
# Check all container status
docker ps -a

# Restart all containers
docker restart $(docker ps -aq)

# View Traefik logs
docker logs traefik --tail 100 -f

# Check Tailscale connectivity
tailscale ping 100.106.57.38
tailscale ping 100.123.199.47

# Test A2A communication
curl http://100.106.57.38:5005/health
curl http://100.123.199.47:5006/health
```
