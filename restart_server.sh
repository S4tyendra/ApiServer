#!/bin/bash

# Kill the existing hypercorn process
pkill -f "hypercorn main:app"

# Wait a moment for the process to terminate
sleep 2

# Start the server again
hypercorn main:app -b localhost:5001 > server.log 2>&1 &
