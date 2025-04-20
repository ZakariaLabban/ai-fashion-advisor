FROM grafana/grafana:latest

COPY datasource.yml /etc/grafana/provisioning/datasources/
COPY dashboards/dashboard.yml /etc/grafana/provisioning/dashboards/
COPY dashboards/fashion_ai_dashboard.json /etc/grafana/dashboards/

EXPOSE 3000 