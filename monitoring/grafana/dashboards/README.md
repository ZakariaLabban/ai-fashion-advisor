# Fashion Advisor Service Dashboards

This directory contains Grafana dashboards for monitoring the Fashion Advisor application and its microservices.

## Available Dashboards

1. **Style IEP Dashboard** (`style_iep_dashboard.json`)
   - Monitors the Style Classification Internal Endpoint Processor
   - Tracks request volume, processing time, error rates, detected styles distribution
   - Provides insights on style confidence scores and model performance

2. **Feature IEP Dashboard** (`feature_iep_dashboard.json`)
   - Monitors the Feature Extraction Internal Endpoint Processor
   - Tracks extraction requests, processing time, color histogram bins
   - Provides insights on model load times and error rates

3. **EEP Dashboard** (`eep_dashboard.json`)
   - Monitors the Ensemble Execution Processor (the orchestration service)
   - Provides comprehensive view of API endpoints usage
   - Tracks system-wide detections, styles, and recommendation requests
   - Monitors internal service calls performance and error rates

## Using the Dashboards

These dashboards are automatically loaded into Grafana via provisioning. Access them at:

```
http://your-server-ip:3001
```

Default login:
- Username: `admin`
- Password: `admin123`

Navigate to the "Fashion Monitoring" folder to view all dashboards.

## Customization

You can customize these dashboards through the Grafana UI. If you want to make 
changes persistent between container restarts, export modified dashboards and 
save them to this directory, replacing the existing files.

## Metrics Source

All metrics are collected from Prometheus-compatible `/metrics` endpoints 
exposed by each service. The metrics are gathered and stored by Prometheus
and then visualized in these Grafana dashboards. 