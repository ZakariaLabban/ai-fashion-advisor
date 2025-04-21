#!/bin/bash

# Master deployment script for Fashion Advisor App and Monitoring Stack
set -e

# Print a message with a timestamp
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log "Docker is not installed. Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        
        # Add current user to docker group
        sudo usermod -aG docker $USER
        log "Docker installed. You may need to log out and back in for group changes to take effect."
    else
        log "Docker is already installed."
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log "Docker Compose is not installed. Installing Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.6/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        log "Docker Compose installed."
    else
        log "Docker Compose is already installed."
    fi
}

# Deploy the monitoring stack
deploy_monitoring() {
    log "Deploying monitoring stack..."
    
    # Make sure the monitoring network exists
    docker network create monitoring-network 2>/dev/null || true
    
    # Set up and start the monitoring stack
    cd monitoring
    chmod +x setup.sh
    ./setup.sh start
    cd ..
    
    log "Monitoring stack deployed successfully."
}

# Deploy the application
deploy_application() {
    log "Deploying Fashion Advisor application..."
    
    # Move the modified docker-compose file
    cp docker-compose.yml.app docker-compose.yml
    
    # Start the application
    docker-compose up -d
    
    log "Fashion Advisor application deployed successfully."
}

# Main execution
main() {
    log "Starting deployment of Fashion Advisor App with Monitoring..."
    
    check_prerequisites
    deploy_monitoring
    deploy_application
    
    log "Deployment completed successfully."
    log "Access the application: http://localhost:3000"
    log "Access Prometheus: http://localhost:9090"
    log "Access Grafana: http://localhost:3001 (username: admin, password: admin123)"
    
    # For Azure VM deployments, show external access information
    if [ -n "$AZURE_VM" ]; then
        PUBLIC_IP=$(curl -s http://checkip.amazonaws.com)
        log "For external access on Azure VM:"
        log "Application: http://$PUBLIC_IP:3000"
        log "Prometheus: http://$PUBLIC_IP:9090"
        log "Grafana: http://$PUBLIC_IP:3001"
        log "Note: Make sure these ports are open in your Network Security Group."
    fi
}

# Execute main function
main 