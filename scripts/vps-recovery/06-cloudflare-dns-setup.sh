#!/bin/bash
# Cloudflare DNS Setup Script
# Configure DNS records for moltbot.anoniem.cc
# 
# IMPORTANT: Replace API_TOKEN with your actual token before running
# This script uses Cloudflare API v4

set -e

# Configuration - UPDATE THESE
CF_API_TOKEN="${CF_API_TOKEN:-YOUR_CLOUDFLARE_API_TOKEN}"
ZONE_NAME="anoniem.cc"
RECORD_NAME="moltbot"
RECORD_TYPE="A"
# Set this to your VPS public IP
VPS_PUBLIC_IP="${VPS_PUBLIC_IP:-YOUR_VPS_PUBLIC_IP}"
PROXIED="true"  # Enable Cloudflare proxy (orange cloud)

echo "=========================================="
echo "CLOUDFLARE DNS SETUP"
echo "=========================================="

# Validate inputs
if [[ "$CF_API_TOKEN" == "YOUR_CLOUDFLARE_API_TOKEN" ]]; then
    echo "ERROR: Please set CF_API_TOKEN environment variable"
    echo "Usage: CF_API_TOKEN=your_token VPS_PUBLIC_IP=x.x.x.x ./06-cloudflare-dns-setup.sh"
    exit 1
fi

if [[ "$VPS_PUBLIC_IP" == "YOUR_VPS_PUBLIC_IP" ]]; then
    echo "ERROR: Please set VPS_PUBLIC_IP environment variable"
    exit 1
fi

# API Base URL
CF_API="https://api.cloudflare.com/client/v4"

# Function to make API calls
cf_api() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    if [ -n "$data" ]; then
        curl -s -X "$method" "$CF_API$endpoint" \
            -H "Authorization: Bearer $CF_API_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data"
    else
        curl -s -X "$method" "$CF_API$endpoint" \
            -H "Authorization: Bearer $CF_API_TOKEN" \
            -H "Content-Type: application/json"
    fi
}

# 1. Get Zone ID
echo "=== Getting Zone ID for $ZONE_NAME ==="
ZONE_RESPONSE=$(cf_api GET "/zones?name=$ZONE_NAME")
ZONE_ID=$(echo "$ZONE_RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$ZONE_ID" ]; then
    echo "ERROR: Could not find zone for $ZONE_NAME"
    echo "Response: $ZONE_RESPONSE"
    exit 1
fi
echo "Zone ID: $ZONE_ID"

# 2. Check if record already exists
echo ""
echo "=== Checking for existing record ==="
FULL_RECORD="${RECORD_NAME}.${ZONE_NAME}"
EXISTING=$(cf_api GET "/zones/$ZONE_ID/dns_records?name=$FULL_RECORD&type=$RECORD_TYPE")
RECORD_ID=$(echo "$EXISTING" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

# 3. Create or Update DNS Record
echo ""
if [ -n "$RECORD_ID" ]; then
    echo "=== Updating existing DNS record ==="
    RESULT=$(cf_api PUT "/zones/$ZONE_ID/dns_records/$RECORD_ID" \
        "{\"type\":\"$RECORD_TYPE\",\"name\":\"$RECORD_NAME\",\"content\":\"$VPS_PUBLIC_IP\",\"ttl\":1,\"proxied\":$PROXIED}")
else
    echo "=== Creating new DNS record ==="
    RESULT=$(cf_api POST "/zones/$ZONE_ID/dns_records" \
        "{\"type\":\"$RECORD_TYPE\",\"name\":\"$RECORD_NAME\",\"content\":\"$VPS_PUBLIC_IP\",\"ttl\":1,\"proxied\":$PROXIED}")
fi

# Check result
SUCCESS=$(echo "$RESULT" | grep -o '"success":true' || echo "")
if [ -n "$SUCCESS" ]; then
    echo "✅ DNS record configured successfully!"
    echo ""
    echo "Record: $FULL_RECORD"
    echo "Type: $RECORD_TYPE"
    echo "Content: $VPS_PUBLIC_IP"
    echo "Proxied: $PROXIED"
else
    echo "❌ Failed to configure DNS record"
    echo "Response: $RESULT"
    exit 1
fi

# 4. Also create CNAME for www subdomain (optional)
echo ""
echo "=== Creating www CNAME (optional) ==="
WWW_RESULT=$(cf_api POST "/zones/$ZONE_ID/dns_records" \
    "{\"type\":\"CNAME\",\"name\":\"www.$RECORD_NAME\",\"content\":\"$FULL_RECORD\",\"ttl\":1,\"proxied\":$PROXIED}" 2>/dev/null)

echo ""
echo "=========================================="
echo "CLOUDFLARE DNS SETUP COMPLETE"
echo "=========================================="
echo ""
echo "DNS propagation may take a few minutes."
echo "Test with: curl -I https://$FULL_RECORD"
echo ""
