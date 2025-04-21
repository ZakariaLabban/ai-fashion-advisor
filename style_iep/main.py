import os
import time
import logging
import io
import numpy as np
import cv2
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import torch
from ultralytics import YOLO
# Import Prometheus libraries
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Style Classification IEP",
    description="Internal Endpoint Processor for clothing style classification using YOLOv8",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define Prometheus metrics
STYLE_REQUESTS = Counter(
    'style_requests_total', 
    'Total number of style classification requests processed'
)
STYLE_ERRORS = Counter(
    'style_errors_total', 
    'Total number of errors during style classification'
)
STYLE_PROCESSING_TIME = Histogram(
    'style_processing_seconds', 
    'Time spent processing style classification requests',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)
STYLES_DETECTED = Counter(
    'styles_detected_total', 
    'Total number of clothing styles detected',
    ['style_name']
)
MODEL_LOAD_TIME = Gauge(
    'style_model_load_time_seconds', 
    'Time taken to load the style model'
)
STYLE_CONFIDENCE = Histogram(
    'style_confidence', 
    'Confidence scores of detected styles',
    buckets=[0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]
)

# Get model path from environment variable or use default
MODEL_PATH = os.getenv("MODEL_PATH", "/app/models/yolov8_style_model.pt")

# Style classes
STYLE_CLASSES = {
    0: "Casual",
    1: "Formal",
    2: "Other",
    3: "Streetwear",
    4: "athletic wear"
}

# Confidence threshold for classification
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.3"))

# Model instance - will be loaded at startup
style_model = None

# Pydantic models for request/response
class StyleResult(BaseModel):
    style_name: str
    style_id: int
    confidence: float

class StyleResponse(BaseModel):
    styles: List[StyleResult]
    processing_time: float
    image_size: List[int]  # [height, width]

@app.on_event("startup")
async def startup_event():
    """Load the YOLOv8 style model at startup."""
    global style_model
    
    logger.info(f"Loading style model from {MODEL_PATH}")
    try:
        start_time = time.time()
        
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
        
        # Load the YOLO model
        style_model = YOLO(MODEL_PATH)
        
        load_time = time.time() - start_time
        MODEL_LOAD_TIME.set(load_time)
        
        logger.info(f"Style model loaded successfully in {load_time:.2f} seconds")
    except Exception as e:
        logger.error(f"Failed to load style model: {e}")
        # We won't raise here to allow the app to start, but endpoints will fail

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if style_model is None:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "message": "Model not loaded"}
        )
    return {"status": "healthy", "model": "YOLOv8 Style Classification"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return PlainTextResponse(generate_latest(), media_type="text/plain; version=0.0.4; charset=utf-8")

@app.post("/classify", response_model=StyleResponse)
async def classify_style(
    file: UploadFile = File(...),
    confidence: Optional[float] = Form(None)
):
    """
    Classify clothing style in the uploaded image.
    
    Args:
        file: The image file to process
        confidence: Optional confidence threshold override
    
    Returns:
        StyleResponse with list of detected styles and metadata
    """
    # Increment counter for total requests
    STYLE_REQUESTS.inc()
    
    # Check if model is loaded
    if style_model is None:
        STYLE_ERRORS.inc()
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Use specified confidence or default
    conf_threshold = confidence if confidence is not None else CONFIDENCE_THRESHOLD
    
    start_time = time.time()
    
    try:
        # Read image from request
        contents = await file.read()
        image = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
        
        if image is None:
            STYLE_ERRORS.inc()
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Get image dimensions
        img_height, img_width = image.shape[:2]
        
        # Run inference with YOLOv8
        # The imgsz parameter matches what's in the Colab notebook
        results = style_model.predict(image, conf=conf_threshold, imgsz=640)
        
        # Process classifications
        styles = []
        
        for box in results[0].boxes:
            class_id = int(box.cls[0])
            conf = float(box.conf[0])
            
            # Record confidence metric
            STYLE_CONFIDENCE.observe(conf)
            
            # Check if meets confidence threshold
            if conf >= conf_threshold:
                style_name = STYLE_CLASSES[class_id]
                
                # Count detected styles by name
                STYLES_DETECTED.labels(style_name=style_name).inc()
                
                style = StyleResult(
                    style_name=style_name,
                    style_id=class_id,
                    confidence=conf
                )
                styles.append(style)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Record processing time
        STYLE_PROCESSING_TIME.observe(processing_time)
        
        return StyleResponse(
            styles=styles,
            processing_time=processing_time,
            image_size=[img_height, img_width]
        )
    
    except Exception as e:
        # Increment error counter
        STYLE_ERRORS.inc()
        
        logger.error(f"Error during style classification: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, log_level="info")
