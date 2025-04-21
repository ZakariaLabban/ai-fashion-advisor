import os
import traceback
import logging
import base64
import shutil
import time
import asyncio
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import httpx
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
FASHN_AI_API_KEY = os.getenv("FASHN_AI_API_KEY", "your_api_key_here")
FASHN_AI_BASE_URL = os.getenv("FASHN_AI_BASE_URL", "https://api.fashn.ai/v1")

logger.info(f"Using FASHN.AI API base URL: {FASHN_AI_BASE_URL}")
logger.info(f"API Key configured: {'Yes' if FASHN_AI_API_KEY != 'your_api_key_here' else 'No'}")

app = FastAPI(
    title="Virtual Try-On IEP",
    description="Internal Endpoint Processor for virtual try-on functionality",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Make sure static directories exist
STATIC_DIR = Path("/app/static")
RESULT_DIR = STATIC_DIR / "results"
UPLOAD_DIR = STATIC_DIR / "uploads"
PLACEHOLDER_DIR = STATIC_DIR / "placeholders"
STATIC_DIR.mkdir(exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PLACEHOLDER_DIR.mkdir(parents=True, exist_ok=True)

# Default placeholder paths
MODEL_PLACEHOLDER = str(PLACEHOLDER_DIR / "model_placeholder.jpg") 
GARMENT_PLACEHOLDER = str(PLACEHOLDER_DIR / "garment_placeholder.jpg")
RESULT_PLACEHOLDER = str(PLACEHOLDER_DIR / "result_placeholder.jpg")

# Mount static files directory
app.mount("/static", StaticFiles(directory="/app/static"), name="static")

# Pydantic models
class TryOnRequest(BaseModel):
    model_image_data: str  # Base64 encoded model image
    garment_image_data: str  # Base64 encoded garment image
    category: str = "auto"  # auto, tops, bottoms, one-pieces
    mode: str = "quality"  # quality, balanced, performance

class TryOnResponse(BaseModel):
    result_image_path: str
    result_image_data: str  # Base64 encoded result image
    details: Dict[str, Any]

class MultiTryOnRequest(BaseModel):
    model_image_data: str  # Base64 encoded model image
    top_image_data: Optional[str] = None  # Base64 encoded top garment
    bottom_image_data: Optional[str] = None  # Base64 encoded bottom garment
    mode: str = "quality"  # quality, balanced, performance

class MultiTryOnResponse(BaseModel):
    final_result_path: str  # Path to the final result image
    final_result_data: str  # Base64 encoded final result image
    details: Dict[str, Any]  # Additional details about the processing

@app.get("/")
async def root():
    """Root endpoint with information about the service"""
    return {
        "service": "Virtual Try-On IEP",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "tryon": "/tryon",
            "multi-tryon": "/tryon/multi",
            "placeholders": {
                "model": "/static/placeholders/model_placeholder.jpg",
                "garment": "/static/placeholders/garment_placeholder.jpg",
                "result": "/static/placeholders/result_placeholder.jpg"
            }
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Virtual Try-On IEP"}

async def run_virtual_tryon(
    model_path: str, 
    garment_path: str,
    result_path: str,
    category: str = "auto",
    mode: str = "quality"
) -> Dict[str, Any]:
    """
    Run a virtual try-on request with FASHN.AI API using the polling approach.
    
    Args:
        model_path: Path to the model image
        garment_path: Path to the garment image
        result_path: Path to save the result image
        category: Category of the garment (auto, tops, bottoms, dresses, outerwear)
        mode: Processing mode (quality, balanced, performance)
    
    Returns:
        Dict containing the result details
    """
    try:
        logger.info(f"Running virtual try-on with model: {model_path}, garment: {garment_path}")
        
        # Validate mode
        valid_modes = ["quality", "balanced", "performance"]
        if mode not in valid_modes:
            logger.warning(f"Invalid mode '{mode}', defaulting to 'quality'")
            mode = "quality"
        
        # Validate category
        valid_categories = ["auto", "tops", "bottoms", "one-pieces"]
        if category not in valid_categories:
            logger.warning(f"Invalid category '{category}', defaulting to 'auto'")
            category = "auto"
        
        # Step 1: Check if files exist
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model image not found at {model_path}")
        if not os.path.exists(garment_path):
            raise FileNotFoundError(f"Garment image not found at {garment_path}")
        
        # Step 2: Convert images to base64 or use URLs
        model_image = None
        garment_image = None
        
        # Check if the images are URLs or local files
        if str(model_path).startswith(("http://", "https://")):
            model_image = model_path
        else:
            with open(model_path, "rb") as image_file:
                model_base64 = base64.b64encode(image_file.read()).decode('utf-8')
                model_image = f"data:image/jpeg;base64,{model_base64}"
        
        if str(garment_path).startswith(("http://", "https://")):
            garment_image = garment_path
        else:
            with open(garment_path, "rb") as image_file:
                garment_base64 = base64.b64encode(image_file.read()).decode('utf-8')
                garment_image = f"data:image/jpeg;base64,{garment_base64}"
        
        # Step 3: Prepare the API request payload
        headers = {
            "Authorization": f"Bearer {FASHN_AI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model_image": model_image,
            "garment_image": garment_image,
            "category": category,
            "moderation_level": "permissive",
            "mode": mode,
            "seed": 42,
            "num_samples": 1
        }
        
        logger.info(f"Sending API request to {FASHN_AI_BASE_URL}/run")
        
        # Step 4: Make the API request to start the prediction
        transport = httpx.AsyncHTTPTransport(retries=3)
        async with httpx.AsyncClient(timeout=120.0, transport=transport) as client:
            response = await client.post(
                f"{FASHN_AI_BASE_URL}/run",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"API error: {response.status_code}, {response.text}")
                raise Exception(f"FASHN.AI API error: {response.status_code}, {response.text}")
            
            result = response.json()
            prediction_id = result.get("id")
            
            if not prediction_id:
                logger.error("No prediction ID returned in response")
                raise Exception("No prediction ID returned in response")
            
            logger.info(f"Prediction started with ID: {prediction_id}")
            
            # Step 5: Poll for prediction status
            status_url = f"{FASHN_AI_BASE_URL}/status/{prediction_id}"
            max_attempts = 120  # 6 minutes (3 seconds between polls)
            
            for attempt in range(max_attempts):
                logger.info(f"Polling status, attempt {attempt+1}/{max_attempts}")
                
                try:
                    # Create a new client for each polling request to avoid connection issues
                    transport = httpx.AsyncHTTPTransport(retries=3)
                    async with httpx.AsyncClient(timeout=30.0, transport=transport) as poll_client:
                        status_response = await poll_client.get(
                            status_url,
                            headers={"Authorization": f"Bearer {FASHN_AI_API_KEY}"}
                        )
                        
                        if status_response.status_code != 200:
                            logger.error(f"Status API error: {status_response.status_code}, {status_response.text}")
                            raise Exception(f"Status API error: {status_response.status_code}, {status_response.text}")
                        
                        status_result = status_response.json()
                        status = status_result.get("status")
                        
                        logger.info(f"Current status: {status}")
                        
                        if status == "completed":
                            # Success! Get the output URLs
                            output_urls = status_result.get("output", [])
                            
                            if not output_urls:
                                logger.error("No output URLs in completed prediction")
                                raise Exception("No output URLs in completed prediction")
                            
                            # Download the first result image
                            result_url = output_urls[0]
                            logger.info(f"Downloading result from {result_url}")
                            
                            # Use a separate client with retries for downloading
                            transport = httpx.AsyncHTTPTransport(retries=3)
                            async with httpx.AsyncClient(timeout=60.0, transport=transport) as download_client:
                                img_response = await download_client.get(result_url)
                                if img_response.status_code != 200:
                                    logger.error(f"Failed to download result image: {img_response.status_code}")
                                    raise Exception(f"Failed to download result image: {img_response.status_code}")
                                
                                # Save the result image
                                os.makedirs(os.path.dirname(os.path.abspath(result_path)), exist_ok=True)
                                with open(result_path, "wb") as f:
                                    f.write(img_response.content)
                                
                                logger.info(f"Result saved to {result_path}")
                                
                                return {
                                    "status": "success",
                                    "prediction_id": prediction_id,
                                    "output_urls": output_urls,
                                    "local_path": result_path,
                                    "category": category,
                                    "mode": mode
                                }
                        
                        elif status == "failed":
                            logger.error("Prediction failed")
                            raise Exception(f"Prediction failed: {status_result.get('error', 'Unknown error')}")
                        
                        # Still processing, wait before polling again
                        await asyncio.sleep(3)
                
                except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.RemoteProtocolError) as e:
                    # Log connection issues but continue polling
                    logger.warning(f"Connection issue during polling (attempt {attempt+1}): {str(e)}")
                    await asyncio.sleep(3)  # Wait a bit before retrying
                    continue
            
            # If we get here, we've timed out
            logger.error("Prediction timed out after maximum polling attempts")
            raise Exception("Prediction timed out after maximum polling attempts")
            
    except Exception as e:
        logger.error(f"Virtual try-on failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Virtual try-on failed: {str(e)}")

async def run_multi_garment_tryon(
    model_path: str,
    top_path: Optional[str],
    bottom_path: Optional[str],
    final_result_path: str,
    mode: str = "quality"
) -> Dict[str, Any]:
    """
    Run a virtual try-on with multiple garments (top and bottom) sequentially.
    
    Args:
        model_path: Path to the model image
        top_path: Path to the top garment image (or None)
        bottom_path: Path to the bottom garment image (or None)
        final_result_path: Path to save the final result image
        mode: The processing mode (quality, balanced, performance)
    
    Returns:
        Dict containing the result details
    """
    try:
        logger.info(f"Running multi-garment try-on with model: {model_path}")
        
        # Validate mode
        valid_modes = ["quality", "balanced", "performance"]
        if mode not in valid_modes:
            logger.warning(f"Invalid mode '{mode}', defaulting to 'quality'")
            mode = "quality"
        
        # Check if at least one garment is provided
        if not top_path and not bottom_path:
            raise ValueError("At least one garment (top or bottom) must be provided")
        
        results = {
            "top_result": None,
            "bottom_result": None,
            "final_result": None
        }
        
        current_model_path = model_path
        
        # Process top garment if provided
        if top_path:
            logger.info(f"Processing top garment: {top_path}")
            
            # Create a temporary file for the interim result if needed
            temp_file = None
            if bottom_path:
                # If we're processing both, use a temporary file for the interim result
                temp_dir = os.path.dirname(final_result_path)
                temp_file = os.path.join(temp_dir, f"temp_{os.path.basename(final_result_path)}")
            else:
                # If we're only processing the top, save directly to the final path
                temp_file = final_result_path
            
            # Run try-on for the top - explicitly use "tops" category
            try:
                top_result = await run_virtual_tryon(
                    current_model_path,
                    top_path,
                    temp_file,
                    category="tops",  # Explicitly set category for tops
                    mode=mode
                )
                
                results["top_result"] = top_result
                
                # If we also have a bottom to process, use the top result as the new model image
                if bottom_path:
                    current_model_path = temp_file
                    logger.info(f"Using interim result as new model image: {current_model_path}")
            except Exception as e:
                logger.error(f"Error processing top garment: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to process top garment: {str(e)}")
        
        # Process bottom garment if provided
        if bottom_path:
            logger.info(f"Processing bottom garment: {bottom_path}")
            
            # Run try-on for the bottom (using either original model or the result of top try-on)
            # Explicitly use "bottoms" category
            try:
                bottom_result = await run_virtual_tryon(
                    current_model_path,
                    bottom_path,
                    final_result_path,
                    category="bottoms",  # Explicitly set category for bottoms
                    mode=mode
                )
                
                results["bottom_result"] = bottom_result
                results["final_result"] = bottom_result
            except Exception as e:
                logger.error(f"Error processing bottom garment: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to process bottom garment: {str(e)}")
            
            # Clean up temporary file if it exists and is not the final result
            if top_path and os.path.exists(temp_file) and temp_file != final_result_path:
                try:
                    os.remove(temp_file)
                    logger.info(f"Removed temporary file: {temp_file}")
                except Exception as e:
                    logger.warning(f"Failed to remove temporary file: {temp_file}, error: {str(e)}")
        elif top_path:
            # If only top was processed, its result is our final result
            results["final_result"] = results["top_result"]
        
        # Get the final image as base64 for the response
        final_result_data = get_base64_image(final_result_path)
        
        logger.info("Multi-garment try-on completed successfully")
        
        return {
            "status": "success",
            "top_processed": top_path is not None,
            "bottom_processed": bottom_path is not None,
            "mode": mode,
            "final_result_path": os.path.basename(final_result_path),
            "final_result_data": final_result_data,
            "results": results
        }
    
    except HTTPException:
        # Pass through HTTP exceptions from nested function calls
        raise
    except Exception as e:
        logger.error(f"Multi-garment try-on failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Multi-garment try-on failed: {str(e)}")

def save_base64_image(base64_data: str, save_path: str) -> str:
    """Save base64 encoded image to a file"""
    try:
        # Remove data URL header if present
        if ',' in base64_data:
            base64_data = base64_data.split(',', 1)[1]
        
        # Decode and save
        with open(save_path, "wb") as f:
            f.write(base64.b64decode(base64_data))
        
        return save_path
    except Exception as e:
        logger.error(f"Error saving base64 image: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid image data: {str(e)}")

def get_base64_image(image_path: str) -> str:
    """Get base64 encoded image from a file"""
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
        return base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        logger.error(f"Error reading image file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to read result image: {str(e)}")

@app.post("/tryon", response_model=TryOnResponse)
async def virtual_tryon_endpoint(request: TryOnRequest):
    """
    Perform virtual try-on with a model image and a garment image.
    
    Args:
        request: TryOnRequest containing base64 encoded images and options
    
    Returns:
        TryOnResponse with the result image and details
    """
    try:
        logger.info(f"Received try-on request: category={request.category}, mode={request.mode}")
        
        # Generate file names with timestamp
        timestamp = int(time.time())
        model_path = str(UPLOAD_DIR / f"model_{timestamp}.jpg")
        garment_path = str(UPLOAD_DIR / f"garment_{timestamp}.jpg")
        result_path = str(RESULT_DIR / f"result_{timestamp}.jpg")
        
        # Save base64 images to files
        save_base64_image(request.model_image_data, model_path)
        save_base64_image(request.garment_image_data, garment_path)
        
        # Run virtual try-on
        result_details = await run_virtual_tryon(
            model_path,
            garment_path,
            result_path,
            category=request.category,
            mode=request.mode
        )
        
        # Get result image as base64
        result_image_data = get_base64_image(result_path)
        
        # Construct relative path
        relative_path = f"/static/results/result_{timestamp}.jpg"
        
        return TryOnResponse(
            result_image_path=relative_path,
            result_image_data=result_image_data,
            details=result_details
        )
    
    except Exception as e:
        logger.error(f"Error in virtual try-on endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Virtual try-on failed: {str(e)}")

@app.post("/tryon/multi", response_model=MultiTryOnResponse)
async def multi_garment_tryon_endpoint(request: MultiTryOnRequest):
    """
    Perform virtual try-on with a model image and multiple garments (top and bottom).
    
    Args:
        request: MultiTryOnRequest containing base64 encoded images and options
    
    Returns:
        MultiTryOnResponse with the result image and details
    """
    try:
        logger.info(f"Received multi-garment try-on request: mode={request.mode}")
        
        # Validate that at least one garment is provided
        if not request.top_image_data and not request.bottom_image_data:
            raise HTTPException(
                status_code=400, 
                detail="At least one garment (top or bottom) must be provided"
            )
        
        # Generate file names with timestamp
        timestamp = int(time.time())
        model_path = str(UPLOAD_DIR / f"model_{timestamp}.jpg")
        top_path = None
        bottom_path = None
        result_path = str(RESULT_DIR / f"result_{timestamp}.jpg")
        
        # Save base64 model image to file
        save_base64_image(request.model_image_data, model_path)
        
        # Save top garment if provided
        if request.top_image_data:
            top_path = str(UPLOAD_DIR / f"top_{timestamp}.jpg")
            save_base64_image(request.top_image_data, top_path)
            logger.info(f"Saved top garment to {top_path}")
        
        # Save bottom garment if provided
        if request.bottom_image_data:
            bottom_path = str(UPLOAD_DIR / f"bottom_{timestamp}.jpg")
            save_base64_image(request.bottom_image_data, bottom_path)
            logger.info(f"Saved bottom garment to {bottom_path}")
        
        # Run multi-garment virtual try-on
        result_details = await run_multi_garment_tryon(
            model_path,
            top_path,
            bottom_path,
            result_path,
            mode=request.mode
        )
        
        # Get result image as base64
        result_image_data = get_base64_image(result_path)
        
        # Construct relative path
        relative_path = f"/static/results/result_{timestamp}.jpg"
        
        return MultiTryOnResponse(
            final_result_path=relative_path,
            final_result_data=result_image_data,
            details=result_details
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in multi-garment try-on endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Multi-garment try-on failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=True) 