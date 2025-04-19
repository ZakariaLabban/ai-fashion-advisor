FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for static files
RUN mkdir -p /app/static/uploads /app/static/results

# Copy application code and static files
COPY . .

# Make sure static files are correctly placed
COPY static/ /app/static/

# Expose port for API
EXPOSE 9000

# Service URLs (can be overridden at runtime)
ENV DETECTION_SERVICE_URL="http://detection-iep:8001"
ENV STYLE_SERVICE_URL="http://style-iep:8002"
ENV FEATURE_SERVICE_URL="http://feature-iep:8003"
ENV VIRTUAL_TRYON_SERVICE_URL="http://virtual-tryon-iep:8004"
ENV ELEGANCE_SERVICE_URL="http://elegance-iep:8005"
ENV RECO_DATA_SERVICE_URL="http://reco-data-iep:8007"
ENV MATCH_SERVICE_URL="http://match-iep:8008"
ENV TEXT2IMAGE_SERVICE_URL="http://text2image-iep:8020"
ENV PPL_DETECTOR_SERVICE_URL="http://ppl-detector-iep:8009"
ENV SERVICE_TIMEOUT="30"
ENV PYTHONUNBUFFERED=1

# Run the FastAPI app on startup
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000", "--log-level", "info"] 