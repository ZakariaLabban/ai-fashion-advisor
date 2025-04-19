import os
import time
import logging
import io
import numpy as np
import cv2
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import torch
from ultralytics import YOLO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Person Detection IEP",
    description="Internal Endpoint Processor for person detection using YOLOv8",
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

# Get model path from environment variable or use default
MODEL_PATH = os.getenv("MODEL_PATH", "/app/models/yolov8n.pt")

# Confidence threshold for detection
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.45"))

# COCO class ID for person
PERSON_CLASS_ID = 0

# Model instance - will be loaded at startup
detection_model = None

# Pydantic models for request/response
class PersonDetection(BaseModel):
    confidence: float
    bbox: List[int]  # [x1, y1, x2, y2]
    crop_data: Optional[str] = None  # Base64 encoded image crop (optional)

class DetectionResponse(BaseModel):
    person_count: int
    detections: List[PersonDetection]
    processing_time: float
    image_size: List[int]  # [height, width]

@app.on_event("startup")
async def startup_event():
    """Load the YOLOv8 model at startup."""
    global detection_model
    
    logger.info(f"Loading person detection model from {MODEL_PATH}")
    try:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
        
        # Load the YOLO model
        detection_model = YOLO(MODEL_PATH)
        logger.info("Person detection model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load person detection model: {e}")
        # We won't raise here to allow the app to start, but endpoints will fail

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if detection_model is None:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "message": "Model not loaded"}
        )
    return {"status": "healthy", "model": "YOLOv8 Person Detection"}

@app.post("/detect", response_model=DetectionResponse)
async def detect_persons(
    file: UploadFile = File(...),
    include_crops: bool = Form(False),
    confidence: Optional[float] = Form(None)
):
    """
    Detect persons in the uploaded image.
    
    Args:
        file: The image file to process
        include_crops: Whether to include cropped images in the response
        confidence: Optional confidence threshold override
    
    Returns:
        DetectionResponse with count of persons and metadata
    """
    # Check if model is loaded
    if detection_model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Use specified confidence or default
    conf_threshold = confidence if confidence is not None else CONFIDENCE_THRESHOLD
    
    start_time = time.time()
    
    try:
        # Read image from request
        contents = await file.read()
        image = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Get image dimensions
        img_height, img_width = image.shape[:2]
        
        # Run inference with YOLOv8
        results = detection_model.predict(image, conf=conf_threshold)
        
        # Process detections
        detections = []
        
        # Check if we have results
        if len(results) > 0:
            # Access boxes from the first result
            for i, box in enumerate(results[0].boxes):
                class_id = int(box.cls[0])
                conf = float(box.conf[0])
                
                # Check if person (class_id = 0) & meets confidence threshold
                if class_id == PERSON_CLASS_ID and conf >= conf_threshold:
                    # Get the bounding box coordinates
                    try:
                        x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                        
                        detection = PersonDetection(
                            confidence=conf,
                            bbox=[x1, y1, x2, y2],
                            crop_data=None  # Will be filled if include_crops is True
                        )
                        
                        # Include crops if requested
                        if include_crops:
                            # Crop the detected person
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
        
        return DetectionResponse(
            person_count=len(detections),
            detections=detections,
            processing_time=processing_time,
            image_size=[img_height, img_width]
        )
    
    except Exception as e:
        logger.error(f"Error during detection: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.post("/count_persons")
async def count_persons(
    file: UploadFile = File(...),
    confidence: Optional[float] = Form(None)
):
    """
    Count the number of persons in the uploaded image.
    
    Args:
        file: The image file to process
        confidence: Optional confidence threshold override
    
    Returns:
        JSON response with count of persons
    """
    # Check if model is loaded
    if detection_model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Use specified confidence or default
    conf_threshold = confidence if confidence is not None else CONFIDENCE_THRESHOLD
    
    try:
        # Read image from request
        contents = await file.read()
        image = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Run inference with YOLOv8
        results = detection_model.predict(image, conf=conf_threshold)
        
        # Count persons (class_id = 0)
        person_count = 0
        if len(results) > 0:
            classes = results[0].boxes.cls.cpu().numpy().astype(int)
            person_count = int((classes == PERSON_CLASS_ID).sum())
        
        return {"person_count": person_count}
    
    except Exception as e:
        logger.error(f"Error during person counting: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8009, log_level="info") 