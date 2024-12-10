#!/bin/bash

# Wait for Grafana to be ready
until curl -s http://grafana:3000/api/health | grep -q '"database": "ok"'; do
    echo "Waiting for Grafana to be ready..."
    sleep 1
done

# Create viewer user using Grafana API
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "login": "'"${GF_VIEWER_LOGIN}"'",
        "password": "'"${GF_VIEWER_PASSWORD}"'",
        "OrgId": 1,
        "role": "Viewer"
    }' \
    http://${GF_SECURITY_ADMIN_USER}:${GF_SECURITY_ADMIN_PASSWORD}@grafana:3000/api/admin/users
