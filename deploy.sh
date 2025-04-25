#!/bin/bash

# Exit on error
set -e

# Navigate to the project directory
cd /home/azureuser/ai-fashion-advisor

# Stop all running containers
echo "Stopping running containers..."
docker-compose down

# Configure git to use the token
git config --global credential.helper store
echo "https://${GITHUB_TOKEN}@github.com" > ~/.git-credentials

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

# Clean up credentials
rm ~/.git-credentials

echo "Deployment completed successfully!" 