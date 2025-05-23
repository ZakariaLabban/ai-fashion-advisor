import os
import time
import logging
import io
import numpy as np
import cv2
import ssl
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
# Import Prometheus libraries
from prometheus_client import Counter, Histogram, Gauge, generate_latest
# Import Azure Blob Helper
from azure_blob_helper import AzureBlobHelper, download_model
# Import Azure Key Vault Helper
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from azure_keyvault_helper import AzureKeyVaultHelper

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

# Define Prometheus metrics
FEATURE_REQUESTS = Counter(
    'feature_extraction_requests_total', 
    'Total number of feature extraction requests processed'
)
FEATURE_ERRORS = Counter(
    'feature_extraction_errors_total', 
    'Total number of errors during feature extraction'
)
FEATURE_PROCESSING_TIME = Histogram(
    'feature_extraction_processing_seconds', 
    'Time spent processing feature extraction requests',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)
MODEL_LOAD_TIME = Gauge(
    'feature_model_load_time_seconds', 
    'Time taken to load the feature extraction model'
)
COLOR_HISTOGRAM_BINS = Gauge(
    'color_histogram_bins_total',
    'Number of bins used in color histograms'
)

# Initialize Azure Key Vault helper
keyvault = AzureKeyVaultHelper()

# Get model path from environment variable or use default
MODEL_PATH = os.getenv("MODEL_PATH", "/app/models/multitask_resnet50_finetuned.pt")
# Azure Blob Storage configuration
MODEL_BLOB_NAME = os.getenv("MODEL_BLOB_NAME", "multitask_resnet50_finetuned.pt")
# Get container name from Key Vault or use default from environment variable
MODEL_CONTAINER_NAME = keyvault.get_secret("MODEL-CONTAINER-NAME", 
                                         os.getenv("MODEL_CONTAINER_NAME", "models"))
# Get Azure Storage Account URL from Key Vault only - no environment variable fallback
AZURE_STORAGE_ACCOUNT_URL = keyvault.get_secret("AZURE-STORAGE-ACCOUNT-URL")

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
    # Convert to RGB for more intuitive histogram
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    
    # Extract individual channels
    r_channel = img_rgb[:, :, 0].flatten()
    g_channel = img_rgb[:, :, 1].flatten()
    b_channel = img_rgb[:, :, 2].flatten()
    
    # Compute histograms for each channel (simpler approach)
    r_hist, _ = np.histogram(r_channel, bins=bins_per_channel, range=(0, 256), density=True)
    g_hist, _ = np.histogram(g_channel, bins=bins_per_channel, range=(0, 256), density=True)
    b_hist, _ = np.histogram(b_channel, bins=bins_per_channel, range=(0, 256), density=True)
    
    # Concatenate for a 1D histogram
    hist = np.concatenate([r_hist, g_hist, b_hist])
    
    # Normalize
    hist = hist / np.sum(hist)
    
    # Log the histogram for debugging
    logger.info(f"Computed color histogram with {len(hist)} bins")
    logger.info(f"RGB bin ranges: R={r_hist}, G={g_hist}, B={b_hist}")
    
    # Find dominant color from histogram for debugging
    r_peak_bin = np.argmax(r_hist)
    g_peak_bin = np.argmax(g_hist)
    b_peak_bin = np.argmax(b_hist)
    
    # Convert bin indices to actual color values
    bin_width = 256 / bins_per_channel
    r_peak = int((r_peak_bin + 0.5) * bin_width)
    g_peak = int((g_peak_bin + 0.5) * bin_width)
    b_peak = int((b_peak_bin + 0.5) * bin_width)
    
    logger.info(f"Dominant color from histogram: RGB({r_peak}, {g_peak}, {b_peak})")
    
    return hist

@app.on_event("startup")
async def startup_event():
    """Load the MultiTaskResNet50 model at startup."""
    global feature_extractor
    
    start_time = time.time()
    model_loaded = False
    model_path = MODEL_PATH
    
    # Initialize the model without downloading ImageNet weights
    feature_extractor = MultiTaskResNet50().eval()
    
    # Try to load from Azure Blob Storage first
    try:
        logger.info(f"Attempting to download model from Azure Blob Storage: container={MODEL_CONTAINER_NAME}, blob={MODEL_BLOB_NAME}")
        model_path = download_model(
            container_name=MODEL_CONTAINER_NAME,
            blob_name=MODEL_BLOB_NAME,
            local_path=MODEL_PATH
        )
        logger.info(f"Successfully downloaded model from Azure Blob Storage to {model_path}")
        model_loaded = True
    except Exception as e:
        logger.warning(f"Failed to download model from Azure Blob Storage: {e}")
        logger.info("Falling back to local model path if available")
    
    # Check if model file exists locally if Azure download failed
    if not model_loaded and not os.path.exists(MODEL_PATH):
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
    
    # Load the custom model weights
    try:
        logger.info(f"Loading custom model from {model_path}...")
        # Load the checkpoint with error handling
        sd = torch.load(model_path, map_location='cpu')
        
        filtered_sd = {}
        for k, v in sd.items():
            # Keep only base_model.* parameters
            # (i.e. skip "gender_head", "master_head", etc.)
            if "head" not in k:
                filtered_sd[k] = v
        
        # Load the filtered state dict
        load_result = feature_extractor.load_state_dict(filtered_sd, strict=False)
        logger.info(f"Custom feature extractor model loaded successfully with result: {load_result}")
        
        # Record model load time
        load_time = time.time() - start_time
        MODEL_LOAD_TIME.set(load_time)
        
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

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if feature_extractor is None:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "message": "Model not loaded"}
        )
    return {"status": "healthy", "model": "MultiTaskResNet50 Feature Extractor"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return PlainTextResponse(generate_latest(), media_type="text/plain; version=0.0.4; charset=utf-8")

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
    # Increment counter for total requests
    FEATURE_REQUESTS.inc()
    
    # Check if model is loaded
    if feature_extractor is None:
        FEATURE_ERRORS.inc()
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
        
        # Record number of bins
        COLOR_HISTOGRAM_BINS.set(len(color_hist))
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Record processing time
        FEATURE_PROCESSING_TIME.observe(processing_time)
        
        return FeatureResponse(
            features=feature_vector.tolist(),  # Convert to list for JSON serialization
            color_histogram=color_hist.tolist(),  # Convert to list for JSON serialization
            processing_time=processing_time,
            input_image_size=[img_height, img_width]
        )
    
    except Exception as e:
        # Increment error counter
        FEATURE_ERRORS.inc()
        
        logger.error(f"Error during feature extraction: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8003, log_level="info")
