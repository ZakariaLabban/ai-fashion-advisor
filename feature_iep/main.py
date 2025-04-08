import os
import time
import logging
import io
import numpy as np
import cv2
import ssl
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Disable SSL verification for downloading pretrained models
# This is not recommended for production but helps when SSL certificates are expired
ssl._create_default_https_context = ssl._create_unverified_context

# Initialize FastAPI app
app = FastAPI(
    title="Feature Extraction IEP",
    description="Internal Endpoint Processor for clothing feature extraction using MultiTaskResNet50",
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
MODEL_PATH = os.getenv("MODEL_PATH", "/app/models/multitask_resnet50_finetuned.pt")

# Define the MultiTaskResNet50 model class
class MultiTaskResNet50(nn.Module):
    def __init__(self):
        super(MultiTaskResNet50, self).__init__()
        # Initialize with dummy weights first, we'll load the real weights from the file
        self.base_model = models.resnet50(weights=None)
        
        num_features = self.base_model.fc.in_features
        self.base_model.fc = nn.Identity()  # Output a 2048-d vector

        # Dummy heads – we won't use them, but let's define them for compatibility
        self.gender_head = nn.Linear(num_features, 2)
        self.master_head = nn.Linear(num_features, 6)
        self.sub_head = nn.Linear(num_features, 15)
        self.article_head = nn.Linear(num_features, 25)
        self.base_head = nn.Linear(num_features, 10)
        self.season_head = nn.Linear(num_features, 4)
        self.usage_head = nn.Linear(num_features, 5)

    def forward(self, x):
        feats = self.base_model(x)  # shape: (batch, 2048)
        # The heads won't matter for this pipeline
        return feats

# Transform for ResNet-based feature extraction
feature_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=(0.485, 0.456, 0.406),
        std=(0.229, 0.224, 0.225)
    )
])

# Global variable for model
feature_extractor = None

# Pydantic models for requests/responses
class FeatureResponse(BaseModel):
    features: List[float]
    color_histogram: List[float]
    processing_time: float
    input_image_size: List[int]  # [height, width]

def extract_features(tensor):
    """Extract the 2048-d feature vector from a preprocessed image tensor."""
    # tensor shape: (1,3,224,224)
    with torch.no_grad():
        out = feature_extractor.base_model(tensor)  # (1, 2048)
    return out.squeeze().cpu().numpy()

def compute_color_histogram(img_bgr, bins_per_channel=8):
    """
    Compute a color histogram in HSV color space.
    Return shape (bins_per_channel^3,).
    """
    img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    histSize = [bins_per_channel, bins_per_channel, bins_per_channel]
    ranges = [0, 180, 0, 256, 0, 256]  # HSV
    channels = [0, 1, 2]
    hist = cv2.calcHist([img_hsv], channels, None, histSize, ranges)
    cv2.normalize(hist, hist, alpha=1, beta=0, norm_type=cv2.NORM_L1)
    return hist.flatten()

@app.on_event("startup")
async def startup_event():
    """Load the MultiTaskResNet50 model at startup."""
    global feature_extractor
    
    logger.info(f"Loading feature extractor model from {MODEL_PATH}")
    try:
        # Initialize the model without downloading ImageNet weights
        feature_extractor = MultiTaskResNet50().eval()
        
        # Check if model file exists
        if not os.path.exists(MODEL_PATH):
            logger.error(f"Model file not found at {MODEL_PATH}. Trying to use pretrained ImageNet weights.")
            # If custom model doesn't exist, fallback to ImageNet weights
            try:
                # Create a new model with pretrained weights
                temp_model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
                # Transfer the weights
                feature_extractor.base_model.load_state_dict(temp_model.state_dict(), strict=False)
                logger.info("Successfully loaded ImageNet pretrained weights as fallback")
                del temp_model  # Free memory
            except Exception as e:
                logger.error(f"Failed to load ImageNet weights: {e}")
            return
        
        try:
            logger.info(f"Loading custom model from {MODEL_PATH}...")
            # Load the checkpoint with error handling
            sd = torch.load(MODEL_PATH, map_location='cpu')
            
            filtered_sd = {}
            for k, v in sd.items():
                # Keep only base_model.* parameters
                # (i.e. skip "gender_head", "master_head", etc.)
                if "head" not in k:
                    filtered_sd[k] = v
            
            # Load the filtered state dict
            load_result = feature_extractor.load_state_dict(filtered_sd, strict=False)
            logger.info(f"Custom feature extractor model loaded successfully with result: {load_result}")
        except Exception as e:
            logger.error(f"Error loading model weights: {e}")
            logger.error(f"Detailed traceback:")
            import traceback
            logger.error(traceback.format_exc())
            logger.warning("Will use the model with pretrained ImageNet weights as fallback")
            try:
                # Create a new model with pretrained weights
                temp_model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
                # Transfer the weights
                feature_extractor.base_model.load_state_dict(temp_model.state_dict(), strict=False)
                logger.info("Successfully loaded ImageNet pretrained weights as fallback")
                del temp_model  # Free memory
            except Exception as e:
                logger.error(f"Failed to load ImageNet weights: {e}")
    except Exception as e:
        logger.error(f"Failed to initialize feature extractor model: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # We won't raise here to allow the app to start, but endpoints will fail

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if feature_extractor is None:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "message": "Model not loaded"}
        )
    return {"status": "healthy", "model": "MultiTaskResNet50 Feature Extractor"}

@app.post("/extract", response_model=FeatureResponse)
async def extract_image_features(
    file: UploadFile = File(...),
    bins_per_channel: int = Form(8)
):
    """
    Extract features from an uploaded image.
    
    Args:
        file: The image file to process
        bins_per_channel: Number of bins per channel for color histogram (default=8)
    
    Returns:
        FeatureResponse with feature vector and color histogram
    """
    # Check if model is loaded
    if feature_extractor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    start_time = time.time()
    
    try:
        # Read image from request
        contents = await file.read()
        img_bgr = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
        
        if img_bgr is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Get image dimensions
        img_height, img_width = img_bgr.shape[:2]
        
        # 1. Extract 2048-d feature vector
        # Convert to RGB for PIL
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        
        # Apply transformations and extract features
        img_tensor = feature_transform(pil_img).unsqueeze(0)  # Add batch dimension
        feature_vector = extract_features(img_tensor)
        
        # 2. Compute color histogram
        color_hist = compute_color_histogram(img_bgr, bins_per_channel=bins_per_channel)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        return FeatureResponse(
            features=feature_vector.tolist(),  # Convert to list for JSON serialization
            color_histogram=color_hist.tolist(),  # Convert to list for JSON serialization
            processing_time=processing_time,
            input_image_size=[img_height, img_width]
        )
    
    except Exception as e:
        logger.error(f"Error during feature extraction: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8003, log_level="info")
