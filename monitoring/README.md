# AI Fashion Advisor Monitoring

This directory contains the monitoring setup for the AI Fashion Advisor project using Prometheus and Grafana.

## Components

The monitoring stack consists of the following components:

1. **Prometheus**: Collects metrics from all services
2. **Grafana**: Visualizes metrics in dashboards
3. **Node Exporter**: Collects system metrics from the host

## Directory Structure

```
monitoring/
├── docker-compose.monitoring.yml   # Docker Compose file for the monitoring stack
├── prometheus/
│   └── prometheus.yml              # Prometheus configuration
└── grafana/
    └── provisioning/
        ├── datasources/            # Grafana datasource configurations
        │   └── datasource.yml
        └── dashboards/             # Grafana dashboard configurations
            ├── dashboard.yml
            └── json/               # JSON files for dashboards
                └── fashion-advisor-overview.json
```

## Setup

1. Make sure you have Docker and Docker Compose installed.
2. The main AI Fashion Advisor stack should be running.
3. Start the monitoring stack:

```bash
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

4. Access Prometheus: [http://localhost:9090](http://localhost:9090)
5. Access Grafana: [http://localhost:3001](http://localhost:3001)
   - Default credentials: admin / fashion_advisor

## Available Dashboards

- **AI Fashion Advisor Overview**: Shows key metrics for all services
  - Request rate by service
  - Response time by service
  - CPU usage by service
  - Memory usage by service
  - Error rate by service

## Adding Custom Metrics

Each service in the AI Fashion Advisor project should expose metrics on the `/metrics` endpoint. Here's how to add custom metrics to your services:

### For FastAPI services

1. Install the Prometheus client:

```bash
pip install prometheus-fastapi-instrumentator
```

2. Add the following code to your FastAPI application:

```python
from prometheus_fastapi_instrumentator import Instrumentator

# In your FastAPI app initialization
app = FastAPI()

# Set up Prometheus instrumentation
Instrumentator().instrument(app).expose(app)
```

This will automatically instrument your FastAPI app with default metrics like:
- Request count
- Request duration
- Response size
- Exceptions

### For Custom Metrics

For service-specific metrics, you can use the Prometheus Python client directly:

```python
from prometheus_client import Counter, Histogram, Gauge

# Define your metrics
detection_count = Counter('detection_total', 'Total number of clothing items detected', ['class_name'])
processing_time = Histogram('detection_processing_seconds', 'Time spent processing detection', buckets=[0.1, 0.5, 1, 2, 5, 10])
gpu_memory_usage = Gauge('gpu_memory_usage_bytes', 'GPU memory usage in bytes')

# Use them in your code
detection_count.labels(class_name='shirt').inc()
with processing_time.time():
    # Do processing
    pass
gpu_memory_usage.set(get_gpu_memory_usage())
```

## Alerts

Prometheus is configured with basic alerting rules. You can add more rules by modifying the `prometheus/prometheus.yml` file.

## Maintenance

### Prometheus

To reload Prometheus configuration without restarting:

```bash
curl -X POST http://localhost:9090/-/reload
```

### Grafana

Grafana dashboards are provisioned automatically, but you can also create or modify dashboards through the UI and export them as JSON.

## Troubleshooting

- **No metrics showing up**: Check if services are exposing the `/metrics` endpoint correctly
- **Prometheus not scraping**: Check the targets page in Prometheus UI at `/targets`
- **Grafana can't connect to Prometheus**: Check the datasource configuration 