#!/usr/bin/env bash
# Clarity CBT Bot - Local Development Runner
# Usage: ./run.sh or bash run.sh

set -euo pipefail

# Get script directory (works both locally and in production)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies if needed
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt -q
fi

# Check for required environment variables
if [ -z "${TELEGRAM_BOT_TOKEN:-}" ]; then
    echo "Error: TELEGRAM_BOT_TOKEN is not set"
    echo "Please set it via: export TELEGRAM_BOT_TOKEN=your_token_here"
    exit 1
fi

echo "Starting Clarity CBT Bot..."
echo "Press Ctrl+C to stop"

# Run the bot
exec python src/main.py
