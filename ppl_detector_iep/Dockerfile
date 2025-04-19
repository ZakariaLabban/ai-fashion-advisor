FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create models directory with proper permissions
RUN mkdir -p /app/models && chmod 777 /app/models

# Copy application code
COPY . .

# Set environment variables
ENV MODEL_PATH=/app/models/yolov8n.pt
ENV PYTHONUNBUFFERED=1
ENV CONFIDENCE_THRESHOLD=0.45

# Debug command to check model existence during build
RUN echo "Models directory contents:" && ls -la /app/models

# Expose port for API
EXPOSE 8009

# Run the FastAPI app on startup
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8009", "--log-level", "info"] 