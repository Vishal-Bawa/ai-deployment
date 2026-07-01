#!/bin/bash
# Basic server security hardening for a fresh Ubuntu VPS.
# Run this ONCE on the server before deploying — not needed for pure local dev.
# Usage: sudo ./server_hardening.sh

set -euo pipefail

echo "=== Updating system packages ==="
apt-get update && apt-get upgrade -y

echo "=== Installing firewall (ufw) and fail2ban ==="
apt-get install -y ufw fail2ban

echo "=== Configuring firewall rules ==="
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "=== Enabling fail2ban (protects SSH from brute force) ==="
systemctl enable fail2ban
systemctl start fail2ban

echo "=== Disabling root SSH login and password auth (key-only) ==="
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd

echo "=== Installing Docker (if not already installed) ==="
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker "$SUDO_USER"
fi

echo "=== Done. Log out and back in for docker group changes to apply. ==="
echo "=== Firewall status: ==="
ufw status verbose
