#!/bin/bash

# List of IEP directories
services=(
    "detection_iep"
    "style_iep"
    "feature_iep"
    "virtual_tryon_iep"
    "elegance_iep"
    "match_iep"
    "reco_data_iep"
    "text2image_iep"
    "ppl_detector_iep"
)

# Add Prometheus dependencies to each service's requirements.txt
for service in "${services[@]}"; do
    if [ -f "$service/requirements.txt" ]; then
        echo "Updating $service/requirements.txt"
        # Check if dependencies already exist
        if ! grep -q "prometheus-client" "$service/requirements.txt"; then
            echo "prometheus-client==0.16.0" >> "$service/requirements.txt"
        fi
        if ! grep -q "prometheus-fastapi-instrumentator" "$service/requirements.txt"; then
            echo "prometheus-fastapi-instrumentator==6.0.0" >> "$service/requirements.txt"
        fi
    else
        echo "Warning: $service/requirements.txt not found"
    fi
done

echo "All services updated with Prometheus dependencies" 