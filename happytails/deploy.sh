#!/bin/bash
# Deploy HappyTails stack with environment variables from .env

set -e

# Load environment variables from .env file
if [ -f .env ]; then
    echo "Loading environment variables from .env..."
    set -a
    source .env
    set +a
else
    echo "Error: .env file not found!"
    exit 1
fi

# Deploy the stack
echo "Deploying happytails stack..."
docker stack deploy -c docker-compose.yml happytails

echo "Deployment complete!"
echo "Check status with: docker service ls"
