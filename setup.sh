#!/bin/bash

# SIMCO AI - Infrastructure Setup Script

echo "Initializing SIMCO AI Environment..."

# 1. Check/Install nmap (MacOS specific for dev environment)
if ! command -v nmap &> /dev/null; then
    echo "nmap not found. Attempting to install via Homebrew..."
    if command -v brew &> /dev/null; then
        brew install nmap
    else
        echo "Homebrew not found. Please install nmap manually: https://nmap.org/download.html"
    fi
else
    echo "nmap is already installed."
fi

# 2. Python Virtual Environment
echo "Setting up Python Virtual Environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

# 3. Install Dependencies
echo "Installing dependencies..."
source venv/bin/activate
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "requirements.txt not found!"
fi

echo "Setup Complete. Activate venv with: source venv/bin/activate"
