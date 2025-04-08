FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user to run the app
RUN adduser --disabled-password --gecos "" appuser

# Create necessary directories with proper permissions
RUN mkdir -p /app/static/conversations && \
    chown -R appuser:appuser /app/static && \
    chmod -R 777 /app/static/conversations

# Copy application code
COPY . .

# Ensure permissions
RUN chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Expose port
EXPOSE 8005

# Switch to non-root user
USER appuser

# Start server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005", "--reload"] 