# Fashion AI Advisor Monitoring

This directory contains a monitoring setup for the Fashion AI Advisor project using Prometheus and Grafana.

## Components

* **Prometheus** - For collecting metrics from services
* **Grafana** - For visualizing metrics in dashboards
* **Service Monitor** - A custom service that checks the health of all services and exposes metrics for Prometheus

## Setup Instructions

1. Make sure your Fashion AI Advisor is running (`docker-compose up -d` in the root directory)
2. Start the monitoring stack:

```bash
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

3. Access the services:
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3001 (default credentials: admin/admin)

## Available Metrics

The monitoring setup collects the following metrics:

- `service_up` - Service health status (1=up, 0=down)
- `api_latency` - API response time in seconds
- `api_requests` - Count of API requests

## Dashboards

A default dashboard is provided that gives an overview of service health status. You can customize or create additional dashboards in Grafana.

## Troubleshooting

If the services cannot connect to each other, ensure that the `fashion-network` name in `docker-compose.monitoring.yml` matches your actual Docker network name. You can check your Docker networks with:

```bash
docker network ls
```

## Customization

To monitor additional endpoints or services, edit the `SERVICES` dictionary in `service_monitor.py`. 