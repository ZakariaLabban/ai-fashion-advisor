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
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
        
        # Load the YOLO model
        style_model = YOLO(MODEL_PATH)
        logger.info("Style model loaded successfully")
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
    # Check if model is loaded
    if style_model is None:
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
        # The imgsz parameter matches what's in the Colab notebook
        results = style_model.predict(image, conf=conf_threshold, imgsz=640)
        
        # Process classifications
        styles = []
        
        for box in results[0].boxes:
            class_id = int(box.cls[0])
            conf = float(box.conf[0])
            
            # Check if meets confidence threshold
            if conf >= conf_threshold:
                style = StyleResult(
                    style_name=STYLE_CLASSES[class_id],
                    style_id=class_id,
                    confidence=conf
                )
                styles.append(style)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        return StyleResponse(
            styles=styles,
            processing_time=processing_time,
            image_size=[img_height, img_width]
        )
    
    except Exception as e:
        logger.error(f"Error during style classification: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, log_level="info")
