# Use grafana image
FROM grafana/grafana-oss

# Copy the provisioning files into the container
COPY ./provisioning /etc/grafana/provisioning

# Copy the dashboard files into the container
COPY ./dashboards /etc/grafana/dashboards

# Execute the original entrypoint script
CMD ["./run.sh"]
