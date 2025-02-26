#!/bin/bash

# Change to the script's directory
cd "$(dirname "$0")"

# Kill the existing hypercorn process
pkill -f "hypercorn main:app"

# Wait and make sure the process is killed
for i in {1..5}; do
    if pgrep -f "hypercorn main:app" > /dev/null; then
        echo "Waiting for hypercorn to stop..."
        sleep 1
    else
        break
    fi
done

# Force kill if still running
if pgrep -f "hypercorn main:app" > /dev/null; then
    echo "Force killing hypercorn..."
    pkill -9 -f "hypercorn main:app"
    sleep 1
fi

# Start the server again
echo "Starting server..."
nohup hypercorn main:app -b localhost:5001 > server.log 2>&1 &

# Wait to check if server started successfully
sleep 2
if pgrep -f "hypercorn main:app" > /dev/null; then
    echo "Server started successfully"
else
    echo "Failed to start server"
    exit 1
fi
