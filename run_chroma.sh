#!/bin/bash

# Default values
DEFAULT_HOST="localhost"
DEFAULT_PORT=3600

# Get host and port from command line arguments, if provided
HOST=${1:-$DEFAULT_HOST}
PORT=${2:-$DEFAULT_PORT}

# Run the chroma command with the specified or default host and port
chroma run --path /app/chroma_prod --host "$HOST" --port "$PORT"
