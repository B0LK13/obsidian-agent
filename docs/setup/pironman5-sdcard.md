# Pironman5 SD Card Prep (Ubuntu 24.04 LTS)

This guide prepares the SD card's `system-boot` partition so the Pi can
self-provision on first boot using cloud-init and systemd.

## What You Get

- cloud-init seed files (`user-data`, `meta-data`, optional `network-config`)
- config.txt append block for PCIe/I2C/SPI
- first-boot bootstrap scripts that set up NVMe mounts and Pironman folders

## Prerequisites

- Ubuntu Server **or** Ubuntu Desktop 24.04 LTS (Raspberry Pi, ARM64) image flashed to SD card
- SSH public key
- Optional: Wi-Fi SSID + PSK

## Prepare the SD Card

1. Insert the flashed SD card so the `system-boot` partition is mounted.
2. Run the helper script:

   .\scripts\pironman5-sdcard\apply.ps1 -SshPublicKey "ssh-ed25519 AAAA..." -Hostname "pironman5" -Username "ubuntu"

   Optional arguments:
   - `-BootPath "E:\\"` if the label is not `system-boot`
   - `-WifiSsid "YourSSID" -WifiPsk "YourPassword"`
   - `-ForceNetworkConfig` to always write `network-config` for Ethernet
   - `-InstanceId "pironman5-pi-20260127"` to force cloud-init to re-run on previously booted images

3. Safely eject the SD card and boot the Pi.

## What Happens on First Boot

- cloud-init installs base packages and writes bootstrap scripts.
- `bootstrap.service` runs once, provisioning:
  - firmware config block (if missing)
  - NVMe partition + filesystem + mount + bind mounts
  - Pironman directory layout in `/opt/pironman`

Logs: `/var/log/bootstrap.log`

## Deployment Readiness Checklist

- `system-boot/user-data` and `system-boot/meta-data` exist on the SD card
- `config.txt` contains the Pironman5 block (PCIe/I2C/SPI)
- SSH enabled (the template installs `openssh-server` and enables `ssh`)
- NVMe detected and mounted to `/mnt/nvme` after first boot

## Desktop Image Notes

- This works with Ubuntu Desktop 24.04 LTS (Raspberry Pi) using cloud-init.
- If the SD card has **already booted** a Desktop image before, cloud-init may
  skip provisioning. Use `-InstanceId` (default is timestamped) to trigger a
  new cloud-init run. If it still does not run, boot the Pi and run:
  `sudo cloud-init clean --logs && sudo reboot`

## Notes / TODO

- Review `scripts/pironman5-sdcard/system-boot/config.txt.append` for the correct
  overlay required by your NVMe HAT and Pironman5 enclosure.
- Place Pironman systemd units in `/opt/pironman/systemd` (on the image or later)
  to enable fan/OLED/power services.
