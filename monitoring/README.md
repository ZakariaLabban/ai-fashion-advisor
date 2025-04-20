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
   - Prometheus: http://[your-vm-ip]:9090
   - Grafana: http://[your-vm-ip]:3001 (default credentials: admin/admin)

## Available Metrics

The monitoring setup collects the following metrics:

- `service_up` - Service health status (1=up, 0=down)
- `api_latency` - API response time in seconds
- `api_requests` - Count of API requests
- `service_info` - Service information including version and model details

## Dashboards

A default dashboard is provided that gives an overview of:
- Service health status
- Response times for health endpoints
- API request distribution
- Non-200 error responses
- Total request counts by service
- Service information (versions and models)

You can customize or create additional dashboards in Grafana.

## Architecture

The monitoring setup uses a centralized approach:
1. The Service Monitor checks health endpoints of all services
2. Metrics are exposed by the Service Monitor on port 8000
3. Prometheus scrapes metrics from the Service Monitor
4. Grafana visualizes the data from Prometheus

This approach avoids the need to modify the existing services to support Prometheus metrics.

## Troubleshooting

If the services cannot connect to each other, ensure that the `fashion-network` name in `docker-compose.monitoring.yml` matches your actual Docker network name. You can check your Docker networks with:

```bash
docker network ls
```

If you see "DOWN" status for services that you know are running, check:
1. Service endpoints defined in the service_monitor.py file
2. Network connectivity between the service-monitor and your services
3. The logs for more detailed error information:
   ```
   docker-compose -f docker-compose.monitoring.yml logs service-monitor
   ```

## Customization

To monitor additional endpoints or services, edit the `SERVICES` dictionary in `service_monitor.py`. Each service can have multiple endpoints and additional metadata like expected model names. 