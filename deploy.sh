#!/bin/bash

# Exit on error
set -e

# Navigate to the project directory
cd /home/azureuser/ai-fashion-advisor

# Stop all running containers
echo "Stopping running containers..."
docker-compose down

# Pull latest changes
echo "Pulling latest changes..."
git pull origin actions

# Rebuild and start containers
echo "Rebuilding and starting containers..."
docker-compose build --no-cache
docker-compose up -d

# Verify containers are running
echo "Verifying containers are running..."
docker-compose ps

echo "Deployment completed successfully!" 