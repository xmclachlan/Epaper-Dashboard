#!/bin/bash

# Navigate to the dashboard directory
cd /home/pi/epaper-dash

# Activate the virtual environment
source venv/bin/activate

# Run the dashboard script
# We use 'exec' to replace the shell with the python process
exec python3 dashboard.py
