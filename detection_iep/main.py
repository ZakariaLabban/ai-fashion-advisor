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
    title="Clothing Detection IEP",
    description="Internal Endpoint Processor for clothing item detection using YOLOv8",
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
DETECTION_REQUESTS = Counter(
    'detection_requests_total', 
    'Total number of detection requests processed'
)
DETECTION_ERRORS = Counter(
    'detection_errors_total', 
    'Total number of errors during detection'
)
DETECTION_PROCESSING_TIME = Histogram(
    'detection_processing_seconds', 
    'Time spent processing detection requests',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)
ITEMS_DETECTED = Counter(
    'items_detected_total', 
    'Total number of clothing items detected',
    ['class_name']
)
MODEL_LOAD_TIME = Gauge(
    'model_load_time_seconds', 
    'Time taken to load the model'
)
DETECTION_CONFIDENCE = Histogram(
    'detection_confidence', 
    'Confidence scores of detected items',
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]
)

# Get model path from environment variable or use default
MODEL_PATH = os.getenv("MODEL_PATH", "/app/models/yolov8_clothing_detection_segmentation.pt")

# Desired classes to detect
DESIRED_CLASSES = {
    1: "1",
    2: "Shoes",
    3: "3",
    4: "Shirt",
    6: "Socks",
    7: "7",
    9: "Accessory",
    10: "Pants/Shorts",
    11: "Hat",
    12: "12",
    13: "13",
    15: "Dress",
    16: "Jumpsuit",
    17: "Jacket",
    19: "19"
}

# Confidence threshold for detection
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.55"))

# Model instance - will be loaded at startup
detection_model = None

# Pydantic models for request/response
class DetectionResult(BaseModel):
    class_name: str
    class_id: int
    confidence: float
    bbox: List[int]  # [x1, y1, x2, y2]
    crop_data: Optional[str] = None  # Base64 encoded image crop (optional)

class DetectionResponse(BaseModel):
    detections: List[DetectionResult]
    processing_time: float
    image_size: List[int]  # [height, width]

@app.on_event("startup")
async def startup_event():
    """Load the YOLOv8 model at startup."""
    global detection_model
    
    logger.info(f"Loading detection model from {MODEL_PATH}")
    try:
        start_time = time.time()
        
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
        
        # Load the YOLO model
        detection_model = YOLO(MODEL_PATH)
        
        load_time = time.time() - start_time
        MODEL_LOAD_TIME.set(load_time)
        
        logger.info(f"Detection model loaded successfully in {load_time:.2f} seconds")
    except Exception as e:
        logger.error(f"Failed to load detection model: {e}")
        # We won't raise here to allow the app to start, but endpoints will fail

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if detection_model is None:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "message": "Model not loaded"}
        )
    return {"status": "healthy", "model": "YOLOv8 Detection"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return PlainTextResponse(generate_latest(), media_type="text/plain; version=0.0.4; charset=utf-8")

@app.post("/detect", response_model=DetectionResponse)
async def detect_clothing(
    file: UploadFile = File(...),
    include_crops: bool = Form(False),
    confidence: Optional[float] = Form(None)
):
    """
    Detect clothing items in the uploaded image.
    
    Args:
        file: The image file to process
        include_crops: Whether to include cropped images in the response
        confidence: Optional confidence threshold override
    
    Returns:
        DetectionResponse with list of detections and metadata
    """
    # Increment counter for total requests
    DETECTION_REQUESTS.inc()
    
    # Check if model is loaded
    if detection_model is None:
        DETECTION_ERRORS.inc()
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Use specified confidence or default
    conf_threshold = confidence if confidence is not None else CONFIDENCE_THRESHOLD
    
    start_time = time.time()
    
    try:
        # Read image from request
        contents = await file.read()
        image = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
        
        if image is None:
            DETECTION_ERRORS.inc()
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Get image dimensions
        img_height, img_width = image.shape[:2]
        
        # Run inference with YOLOv8
        # Use predict method directly, which works for both detection and segmentation models
        results = detection_model.predict(image, conf=conf_threshold)
        
        # Process detections
        detections = []
        
        # Check if we have results
        if len(results) > 0:
            # Access boxes from the first result
            for i, box in enumerate(results[0].boxes):
                class_id = int(box.cls[0])
                conf = float(box.conf[0])
                
                # Record confidence metric
                DETECTION_CONFIDENCE.observe(conf)
                
                # Check if in desired classes & meets confidence threshold
                if class_id in DESIRED_CLASSES and conf >= conf_threshold:
                    # Make sure we can get the bounding box coordinates
                    try:
                        x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                        
                        class_name = DESIRED_CLASSES[class_id]
                        
                        # Count detected items by class
                        ITEMS_DETECTED.labels(class_name=class_name).inc()
                        
                        detection = DetectionResult(
                            class_name=class_name,
                            class_id=class_id,
                            confidence=conf,
                            bbox=[x1, y1, x2, y2],
                            crop_data=None  # Will be filled if include_crops is True
                        )
                        
                        # Include crops if requested
                        if include_crops:
                            # Crop the detected object
                            cropped = image[y1:y2, x1:x2]
                            
                            # Encode the crop as JPEG
                            _, buffer = cv2.imencode('.jpg', cropped)
                            crop_bytes = buffer.tobytes()
                            
                            # Convert to base64 for JSON response
                            import base64
                            detection.crop_data = base64.b64encode(crop_bytes).decode('utf-8')
                        
                        detections.append(detection)
                    except Exception as e:
                        logger.warning(f"Error processing detection {i}: {e}")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Record processing time
        DETECTION_PROCESSING_TIME.observe(processing_time)
        
        return DetectionResponse(
            detections=detections,
            processing_time=processing_time,
            image_size=[img_height, img_width]
        )
    
    except Exception as e:
        # Increment error counter
        DETECTION_ERRORS.inc()
        
        logger.error(f"Error during detection: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, log_level="info")
