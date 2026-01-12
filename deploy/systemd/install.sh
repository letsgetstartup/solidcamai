#!/bin/bash
# deploy/systemd/install.sh
set -e

echo "--- Installing SIMCO AI Agent as systemd service ---"

# 1. Create User
if ! id "simco" &>/dev/null; then
    sudo useradd -r -s /bin/false simco
fi

# 2. Setup Directory
sudo mkdir -p /opt/simco-agent
sudo cp -r . /opt/simco-agent
sudo chown -R simco:simco /opt/simco-agent

# 3. Setup Virtualenv
cd /opt/simco-agent
sudo -u simco python3 -m venv venv
sudo -u simco ./venv/bin/pip install --upgrade pip
sudo -u simco ./venv/bin/pip install -r requirements.txt

# 4. Install Service
sudo cp deploy/systemd/simco-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable simco-agent
sudo systemctl restart simco-agent

echo "✅ SIMCO AI Agent installed and started."
