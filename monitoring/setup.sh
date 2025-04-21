#!/bin/bash

# Setup script for the Fashion Advisor App Monitoring Stack
set -e

# Print a message with a timestamp
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    mkdir -p prometheus/data
    mkdir -p grafana/data
    
    # Set appropriate permissions
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        log "Setting directory permissions..."
        chmod -R 777 prometheus/data
        chmod -R 777 grafana/data
    fi
}

# Pull Docker images
pull_images() {
    log "Pulling required Docker images..."
    docker pull prom/prometheus:v2.46.0
    docker pull prom/node-exporter:v1.6.1
    docker pull gcr.io/cadvisor/cadvisor:v0.47.2
    docker pull grafana/grafana:10.1.4
}

# Verify Docker is installed and running
check_docker() {
    log "Checking if Docker is installed and running..."
    if ! command -v docker &> /dev/null; then
        log "Docker is not installed. Please install Docker and try again."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log "Docker Compose is not installed. Please install Docker Compose and try again."
        exit 1
    fi
}

# Start the monitoring stack
start_monitoring() {
    log "Starting the monitoring stack..."
    docker-compose up -d
    log "Monitoring stack started successfully."
    
    log "Prometheus is available at http://localhost:9090"
    log "Grafana is available at http://localhost:3001"
    log "Default Grafana credentials: admin/admin123"
}

# Main execution
main() {
    log "Setting up the Fashion Advisor App Monitoring Stack..."
    
    # Change to the script directory
    cd "$(dirname "$0")"
    
    check_docker
    create_directories
    pull_images
    
    log "Setup completed successfully."
    
    # Start the monitoring stack if requested
    if [[ "$1" == "start" ]]; then
        start_monitoring
    else
        log "To start the monitoring stack, run: cd monitoring && ./setup.sh start"
    fi
}

# Execute main function with all arguments
main "$@" 