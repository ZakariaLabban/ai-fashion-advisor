Write-Host "Starting Fashion AI Advisor Monitoring Stack..." -ForegroundColor Cyan
docker-compose -f docker-compose.monitoring.yml up -d

Write-Host ""
Write-Host "Monitoring services started:" -ForegroundColor Green
Write-Host "- Prometheus: http://localhost:9090" -ForegroundColor Yellow
Write-Host "- Grafana: http://localhost:3001 (default credentials: admin/admin)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Note: Make sure your Fashion AI Advisor services are running before using the monitoring dashboard." -ForegroundColor Cyan 