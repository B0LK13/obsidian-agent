# AgentX Installation & Configuration Guide for macOS

## 📋 Overview

This development plan will guide you through installing and configuring AgentX on macOS systems, covering both manual and automated deployment methods.

---

## 🎯 Prerequisites

### System Requirements

- macOS 11 (Big Sur) or later

- Administrator/sudo access

- Terminal access

- Active internet connection

### Pre-Installation Checklist

- [ ] Verify macOS version: `sw_vers_`

_

- [ ] Confirm admin privileges

- [ ] Backup important data

- [ ] Review security & privacy settings

---

## 📥 Phase 1: Download & Preparation

### Step 1.1: Obtain Installation Package

```
# Navigate to download directory
cd ~/Downloads

Download AgentX installer (replace with actual URL)
curl -O https://s.agentx.so/installer/agentx-macos.dmg
```

### Step 1.2: Verify Package Integrity

```
# Check file hash (if provided by vendor)
shasum -a 256 agentx-macos.dmg
```

---

## 🔧 Phase 2: Installation

### Method A: GUI Installation

1. **Mount the DMG**
    
    ```
    open agentx-macos.dmg
    ```
    

2. **Run Installer**

- Double-click the `.pkg` installer

- Follow on-screen prompts

- Enter admin credentials when prompted

1. **Grant Permissions**

- System Preferences → Security & Privacy

- Allow AgentX system extensions

- Grant Full Disk Access if required

### Method B: Command Line Installation

```
# Mount the DMG
hdiutil attach agentx-macos.dmg

Install the package
sudo installer -pkg /Volumes/AgentX/AgentX.pkg -target /

Unmount
hdiutil detach /Volumes/AgentX
```

---

## ⚙️ Phase 3: Configuration

### Step 3.1: Create Configuration File

```
# Create config directory
sudo mkdir -p /Library/Application\ Support/AgentX

Create configuration file
sudo nano /Library/Application\ Support/AgentX/config.json
```

### Step 3.2: Basic Configuration Template

_

_`{   "server`_`url": "https://your-server.agentx.io",   "installation_token": "YOUR_TOKEN_HERE",   "organization_id": "YOUR_ORG_ID",   "agent_settings": {     "auto_update": true,     "reporting_interval": 300,     "log_level": "info"   } }`

### Step 3.3: Set Proper Permissions

```
# Set ownership
sudo chown root:wheel /Library/Application\ Support/AgentX/config.json

Set permissions
sudo chmod 600 /Library/Application\ Support/AgentX/config.json
```

---

## 🚀 Phase 4: Service Management

### Start AgentX Service

```
# Load the launch daemon
sudo launchctl load /Library/LaunchDaemons/com.agentx.agent.plist

Start the service
sudo launchctl start com.agentx.agent
```

### Verify Service Status

```
# Check if service is running
sudo launchctl list | grep agentx

View service logs
tail -f /var/log/agentx/agent.log
```

---

## ✅ Phase 5: Verification & Testing

### Step 5.1: Verify Installation

```
# Check agent version
/usr/local/bin/agentx --version

Verify connectivity
/usr/local/bin/agentx test-connection

Check agent status
sudo /usr/local/bin/agentx status
```

### Step 5.2: Validate Configuration

```
# Test configuration
sudo /usr/local/bin/agentx validate-config

View current settings
sudo /usr/local/bin/agentx show-config
```

---

## 🔒 Phase 6: Security Hardening

### macOS Security Settings

1. **System Preferences → Security & Privacy**

- Privacy → Full Disk Access → Add AgentX

- Privacy → Automation → Enable AgentX permissions

1. **Firewall Configuration**
    
    ```
    # Allow AgentX through firewall
    sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/agentx
    sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /usr/local/bin/agentx
    ```
    

---

## 📊 Phase 7: Monitoring & Maintenance

### Regular Health Checks

```
# Create monitoring script
cat > ~/checkagentx.sh << 'EOF'
#!/bin/bash
if sudo launchctl list | grep -q agentx; then
    echo "✅ AgentX is running"
else
    echo "❌ AgentX is not running"
    sudo launchctl start com.agentx.agent
fi
EOF

chmod +x ~/checkagentx.sh
```

### Log Management

```
# View recent logs
tail -n 100 /var/log/agentx/agent.log

Search for errors
grep -i error /var/log/agentx/agent.log
```

---

## 🔄 Phase 8: Updates & Upgrades

### Manual Update Process

```
# Stop the service
sudo launchctl stop com.agentx.agent

Download new version
curl -O https://s.agentx.so/installer/agentx-macos-latest.dmg

Install update
sudo installer -pkg /Volumes/AgentX/AgentX.pkg -target /

Restart service
sudo launchctl start com.agentx.agent
```

---

## 🆘 Troubleshooting

### Common Issues

**Agent Won't Start**

```
# Check permissions
ls -la /Library/LaunchDaemons/com.agentx.agent.plist

Reload daemon
sudo launchctl unload /Library/LaunchDaemons/com.agentx.agent.plist
sudo launchctl load /Library/LaunchDaemons/com.agentx.agent.plist
```

**Connection Issues**

```
# Test network connectivity
ping your-server.agentx.io

Check DNS resolution
nslookup your-server.agentx.io

Verify firewall rules
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --listapps
```

---

## 📝 Post-Installation Checklist

- [ ] Agent service is running

- [ ] Configuration validated

- [ ] Connectivity confirmed

- [ ] Logs are being generated

- [ ] Security permissions granted

- [ ] Monitoring script configured

- [ ] Documentation updated

- [ ] Team notified of deployment

---

## 📚 Additional Resources

- Official Documentation: [AgentX Docs](https://docs.agentx.io/)

- Support Portal: [AgentX Support](https://support.agentx.io/)

- Community Forum: [AgentX Community](https://community.agentx.io/)

---

**Need help with any specific step?** I'm here to guide you through the process! Just let me know which phase you'd like to dive deeper into. 🚀