# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy only requirement-related files
COPY requirements.txt ./

# Install Python dependencies (with no-cache to ensure we get the latest versions)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download CLIP model and processor during build
RUN python3 -c "\
from transformers import CLIPModel, CLIPProcessor; \
CLIPModel.from_pretrained('openai/clip-vit-base-patch32', cache_dir='./models'); \
CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32', cache_dir='./models')"

# Copy application code and credentials
COPY text_to_image.py ./

# Expose desired port
EXPOSE 8020

# Run the FastAPI app
CMD ["uvicorn", "text_to_image:app", "--host", "0.0.0.0", "--port", "8020"]
