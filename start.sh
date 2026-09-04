#!/bin/bash
# Win Spares Document Management System Launcher

# Navigate to project directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

echo "=================================================="
echo " Starting Win Spares Document Management System   "
echo " URL: http://127.0.0.1:5000                       "
echo "=================================================="

# Automatically open default browser after 1.5s delay
(sleep 1.5 && (xdg-open http://127.0.0.1:5000 || python3 -m webbrowser http://127.0.0.1:5000)) &

# Start Flask application
python app.py
