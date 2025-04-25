#!/bin/bash

# Exit immediately if any command fails
set -e

# Navigate to the project directory
cd /home/azureuser/ai-fashion-advisor

echo "Stopping running containers..."
docker-compose down || true

# Ensure SSH agent is running and key is loaded
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa

# Make sure the remote URL is set to SSH (safe to re-run)
git remote set-url origin git@github.com:ZakariaLabban/ai-fashion-advisor.git

echo "Pulling latest changes from main branch..."
git pull origin main

echo "Rebuilding and starting containers..."
docker-compose build
docker-compose up -d

echo "Verifying containers are running..."
docker-compose ps

echo "✅ Deployment completed successfully!"
