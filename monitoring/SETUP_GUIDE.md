# Fashion Advisor System with Monitoring - Deployment Guide

This guide explains how to deploy the Fashion Advisor system along with the Prometheus and Grafana monitoring stack on an Azure VM.

## Prerequisites

- Azure VM with Docker and Docker Compose installed
- Git installed
- At least 8GB RAM and 4 vCPUs recommended
- Ports 3000, 3001, 7000-7009, 7020, 8080, 9090, 9100 available

## Deployment Steps

### 1. Clone the Repository

```bash
# Clone the repository to your Azure VM
git clone https://github.com/your-repo/ai-fashion-advisor.git
cd ai-fashion-advisor
```

### 2. Set Up the Environment

```bash
# Make sure all environment variables are properly set
# Check the .env file if it exists or create one if needed
```

### 3. Start the Main Application

```bash
# Start the fashion advisor services
docker-compose up -d
```

### 4. Start the Monitoring Stack

```bash
# Navigate to the monitoring directory
cd monitoring

# Start the monitoring services
docker-compose up -d
```

### 5. Verify Deployment

After starting both stacks, verify that all services are running:

```bash
# Check the main application services
docker-compose ps

# Check the monitoring services
cd monitoring
docker-compose ps
```

## Accessing the Services

- **Fashion Advisor Frontend**: http://your-vm-ip:3000
- **Prometheus UI**: http://your-vm-ip:9090
- **Grafana Dashboards**: http://your-vm-ip:3001
  - Username: `admin`
  - Password: `admin123`

## Port Mapping Reference

| Service | Internal Port | External Port |
|---------|---------------|--------------|
| Frontend | 80 | 3000 |
| EEP | 9000 | 7000 |
| Detection IEP | 8001 | 7001 |
| Style IEP | 8002 | 7002 |
| Feature IEP | 8003 | 7003 |
| Virtual Try-On IEP | 8004 | 7004 |
| Elegance IEP | 8005 | 7005 |
| Reco Data IEP | 8007 | 7007 |
| Match IEP | 8008 | 7008 |
| People Detector IEP | 8009 | 7009 |
| Text2Image IEP | 8020 | 7020 |
| Prometheus | 9090 | 9090 |
| Grafana | 3000 | 3001 |
| cAdvisor | 8080 | 8080 |
| Node Exporter | 9100 | 9100 |

## Azure VM Security Configuration

Make sure to configure the Network Security Group (NSG) on your Azure VM to allow incoming traffic on the following ports:

- 3000 (Fashion Advisor Frontend)
- 3001 (Grafana)
- 9090 (Prometheus)

You can add these rules through the Azure Portal:
1. Go to your VM in the Azure Portal
2. Click on "Networking"
3. Add inbound port rules for each port listed above

## Monitoring System Management

### Viewing Dashboards

1. Access Grafana at http://your-vm-ip:3001
2. Log in with the default credentials
3. Navigate to Dashboards -> Browse to see the preconfigured dashboards:
   - Fashion Advisor System Overview
   - Fashion Services Dashboard

### Exploring Metrics in Prometheus

Access Prometheus at http://your-vm-ip:9090 to:
- Run custom queries
- View targets and their status
- Check alert rules

### Troubleshooting

If services are not visible in Prometheus:
1. Check that both docker-compose files are running: `docker-compose ps`
2. Verify that all services are on the same network: `docker network inspect fashion-advisor-network`
3. Check Prometheus targets page for any errors: http://your-vm-ip:9090/targets 