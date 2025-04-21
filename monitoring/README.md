# Fashion Advisor App Monitoring Stack

This directory contains the monitoring stack for the Fashion Advisor App, using Prometheus and Grafana.

## Components

- **Prometheus**: Metrics collection and storage
- **Grafana**: Metrics visualization and dashboarding
- **Node Exporter**: Host system metrics collector
- **cAdvisor**: Container metrics collector

## Port Mappings

The following ports are used by the monitoring stack:

- **9090**: Prometheus web interface
- **3001**: Grafana web interface
- **9100**: Node Exporter metrics endpoint
- **8080**: cAdvisor metrics endpoint

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-fashion-advisor.git
   cd ai-fashion-advisor
   ```

2. Run the setup script:
   ```bash
   cd monitoring
   ./setup.sh
   ```

3. Start the monitoring stack:
   ```bash
   ./setup.sh start
   ```

4. Access the services:
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3001 (username: admin, password: admin123)

## Dashboards

The following dashboards are preconfigured:

1. **Node Exporter Dashboard**: System-level metrics (CPU, memory, disk, network)
2. **Docker Containers**: Container-specific metrics
3. **Fashion Advisor App**: Application-specific metrics

## Security Considerations

For production environments:

1. Change default Grafana credentials
2. Restrict access to Prometheus and cAdvisor
3. Set up auth for Prometheus (basic auth or OAuth)
4. Use network segmentation
5. Keep all components updated

## Azure VM Deployment

If you are deploying on Azure VM, make sure to:

1. Open required ports in the Azure Network Security Group
2. Set the appropriate DNS names if needed
3. Configure persistent storage for metrics data