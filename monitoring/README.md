# Fashion Advisor Monitoring Stack

This directory contains a production-ready monitoring setup using Prometheus and Grafana for the Fashion Advisor application.

## Components

- **Prometheus**: Collects metrics from all services and exporters
- **Grafana**: Visualizes metrics in customizable dashboards
- **Node Exporter**: Collects host system metrics (CPU, memory, disk, network)
- **cAdvisor**: Collects container metrics

## Usage

### Starting the Monitoring Stack

```bash
cd monitoring
docker-compose up -d
```

### Accessing Dashboards

- **Prometheus**: http://your-vm-ip:9090
- **Grafana**: http://your-vm-ip:3001

Default Grafana credentials:
- Username: `admin`
- Password: `admin123`

## Monitored Services

The monitoring stack collects metrics from:

1. System services:
   - Node Exporter (host metrics)
   - cAdvisor (container metrics)
   - Frontend (nginx metrics)
   - Prometheus (self-monitoring)

2. Host system metrics:
   - CPU usage
   - Memory usage
   - Disk usage
   - Network I/O

## Available Dashboards

The "Fashion System Monitoring" dashboard provides comprehensive system monitoring with panels for:

- Service status (up/down)
- CPU usage
- Memory usage
- Network input/output
- Disk usage

## Note on Microservice Metrics

Most of the microservices do not currently expose Prometheus-compatible metrics endpoints. Only the frontend service provides `/metrics` endpoint. To monitor additional services with application-specific metrics, each service would need to implement a `/metrics` endpoint using a Prometheus client library for its programming language.

## Troubleshooting

If you encounter errors when starting the monitoring stack:

1. Try pruning Docker resources:
   ```bash
   docker system prune -f
   docker volume prune -f
   ```

2. Remove existing containers if needed:
   ```bash
   docker rm -f prometheus grafana node-exporter cadvisor
   ```

3. Start the monitoring stack again:
   ```bash
   docker-compose up -d
   ```