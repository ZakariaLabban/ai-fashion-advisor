#!/bin/bash

echo "Starting Fashion AI Advisor Monitoring Stack..."
docker-compose -f docker-compose.monitoring.yml up -d

echo ""
echo "Monitoring services started:"
echo "- Prometheus: http://localhost:9090"
echo "- Grafana: http://localhost:3001 (default credentials: admin/admin)"
echo ""
echo "Note: Make sure your Fashion AI Advisor services are running before using the monitoring dashboard." 