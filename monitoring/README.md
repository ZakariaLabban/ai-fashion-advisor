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

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001

Default Grafana credentials:
- Username: `admin`
- Password: `admin123`

## Pre-configured Dashboards

1. **Fashion Advisor System Overview**: Status of all services and system metrics
2. **Fashion Services Dashboard**: Focused on the fashion microservices' performance

## Monitored Services

The monitoring stack collects metrics from all Fashion Advisor microservices, host system, and containers.