# Use official Python base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose the port used by the app
EXPOSE 8008

# Start FastAPI app with uvicorn
CMD ["uvicorn", "match_api:app", "--host", "0.0.0.0", "--port", "8008", "--reload"] 