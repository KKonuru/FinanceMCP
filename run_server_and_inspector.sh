#!/bin/bash

# Activate the virtual environment
source .venv/bin/activate

# Start the server
python main.py &
SERVER_PID=$!

echo "Server is running with PID $SERVER_PID"

# Start the MCP Inspector
npx @modelcontextprotocol/inspector &
INSPECTOR_PID=$!

echo "Inspector is running with PID $INSPECTOR_PID"

# Wait for both processes to finish
wait $SERVER_PID $INSPECTOR_PID
